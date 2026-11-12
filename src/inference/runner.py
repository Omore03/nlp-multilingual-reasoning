"""Sequential pilot CLI with frozen plans, fsynced JSONL, and strict resumption."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import re
import sys
import time

from dotenv import load_dotenv
import yaml

from src.inference.backends import BackendError, MockBackend, OpenRouterBackend, call_with_retries
from src.inference.google_backend import GoogleAIStudioBackend
from src.inference.free_policy import require_free_model, require_google_free_model
from src.inference.contracts import import_selector, load_records, resolve_ids, selector_query
from src.prompting.templates import CONDITIONS, TEMPLATE_VERSION, build_prompt

ROOT = Path(__file__).resolve().parents[2]
RUNNER_VERSION = '1.2.0-google-direct-free'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def relative_path(value):
    if not isinstance(value, str) or not value or Path(value).is_absolute() or '..' in Path(value).parts:
        raise ValueError('Configuration paths must be repository-relative without ..')
    p = (ROOT / value).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError('Path escapes repository')
    return p


def exact_keys(obj, keys, name):
    if not isinstance(obj, dict) or set(obj) != set(keys.split()):
        raise ValueError(f'Unexpected or missing {name} configuration keys; see configs/mock.yaml')


def validate_config(c):
    exact_keys(c, 'data_kind demo_path dev_path output_path conditions strategies shot_count seed selector selector_version model verification_receipt', 'top-level')
    if c['data_kind'] not in ('synthetic', 'real'):
        raise ValueError('data_kind must be synthetic or real')
    if type(c['shot_count']) is not int or c['shot_count'] != 2:
        raise ValueError('Pilot supports shot_count=2 only')
    if type(c['seed']) is not int or not 0 <= c['seed'] <= 2**32-1:
        raise ValueError('seed must be an unsigned 32-bit integer')
    for key, allowed in [('conditions', CONDITIONS), ('strategies', ('random', 'similarity'))]:
        values = c[key]
        if not isinstance(values, list) or not values or any(not isinstance(x, str) or x not in allowed for x in values) or len(set(values)) != len(values):
            raise ValueError(f'Unsupported or duplicate {key}')
    if not isinstance(c['selector'], str) or not re.fullmatch(r'[A-Za-z_][\w.] *:[A-Za-z_]\w*'.replace(' ', ''), c['selector']):
        raise ValueError('selector must be module:function')
    if not isinstance(c['selector_version'], str) or not c['selector_version'].strip():
        raise ValueError('Set a selector_version and update it when external encoder/cache dependencies change')
    for key in ('demo_path', 'dev_path', 'output_path'):
        relative_path(c[key])
    if c['verification_receipt'] is not None:
        relative_path(c['verification_receipt'])
    if c['data_kind'] == 'synthetic':
        if any(not c[k].startswith('tests/fixtures/') for k in ('demo_path', 'dev_path')):
            raise ValueError('Synthetic inputs belong under tests/fixtures/')
        if not c['output_path'].startswith(('results/mock/', 'results/live_smoke/')):
            raise ValueError('Synthetic outputs belong under results/mock/ or results/live_smoke/')
    else:
        if c['demo_path'] != 'data/processed/demo_pool.jsonl' or c['dev_path'] != 'data/processed/dev.jsonl':
            raise ValueError('Real pilot must use the reserved production input paths')
        if c['output_path'] != 'results/pilot_raw.jsonl' or c['selector'].startswith('tests.'):
            raise ValueError('Real pilot requires production selector and results/pilot_raw.jsonl')
        if set(c['conditions']) != set(CONDITIONS) or set(c['strategies']) != {'random', 'similarity'}:
            raise ValueError('Real pilot requires all four conditions and both strategies')
    m = c['model']
    exact_keys(m, 'backend model_id endpoint credential_env route decoding timeout_seconds max_attempts max_retry_wait_seconds free_only max_requests_per_invocation min_request_interval_seconds', 'model')
    if m['backend'] not in ('mock', 'openrouter', 'google_ai_studio'):
        raise ValueError('Supported backends: mock, google_ai_studio, openrouter (legacy)')
    if m['free_only'] is not True:
        raise ValueError('Zero-cost policy requires free_only=true')
    decoding_keys = 'temperature top_p max_tokens seed' + (' reasoning' if m['backend'] == 'openrouter' else '')
    if m['backend'] == 'google_ai_studio':
        decoding_keys += ' thinking_level'
    exact_keys(m['decoding'], decoding_keys, 'decoding')
    if m['backend'] == 'google_ai_studio' and m['decoding']['thinking_level'] != 'minimal':
        raise ValueError('Direct Google Gemma requires thinking_level=minimal')
    if m['backend'] == 'openrouter' and m['decoding']['reasoning'] != {'enabled': False}:
        raise ValueError('Free Gemma pilot requires reasoning.enabled=false')
    for k, lo, hi in [('temperature', 0, 2), ('top_p', 0.000001, 1)]:
        v = m['decoding'][k]
        if type(v) not in (int, float) or not math.isfinite(v) or not lo <= v <= hi:
            raise ValueError(f'Invalid decoding {k}')
    if type(m['decoding']['max_tokens']) is not int or not 1 <= m['decoding']['max_tokens'] <= 16384:
        raise ValueError('max_tokens must be between 1 and 16384 for the selected endpoint')
    if type(m['decoding']['seed']) is not int or not 0 <= m['decoding']['seed'] <= 2**32-1:
        raise ValueError('Invalid decoding seed')
    for k in ('timeout_seconds', 'max_retry_wait_seconds'):
        if type(m[k]) not in (int, float) or not math.isfinite(m[k]) or not 0 < m[k] <= 300:
            raise ValueError(f'Invalid {k}')
    if type(m['max_attempts']) is not int or not 1 <= m['max_attempts'] <= 5:
        raise ValueError('max_attempts must be 1..5')
    if m['backend'] in ('openrouter', 'google_ai_studio'):
        if m['backend'] == 'openrouter':
            require_free_model(m)
        else:
            require_google_free_model(m)
        if type(m['max_requests_per_invocation']) is not int or not 1 <= m['max_requests_per_invocation'] <= 40:
            raise ValueError('Free API invocation budget must be between 1 and 40 requests, including retries')
        interval = m['min_request_interval_seconds']
        if type(interval) not in (int, float) or not math.isfinite(interval) or not 3.1 <= interval <= 60:
            raise ValueError('Free API pacing must be at least 3.1 seconds per request')
        if not c['output_path'].startswith('results/live_smoke/') and c['data_kind'] == 'synthetic':
            raise ValueError('Live synthetic calls must write under results/live_smoke/')
    elif c['data_kind'] != 'synthetic' or not c['output_path'].startswith('results/mock/'):
        raise ValueError('Mock backend is restricted to synthetic inputs and results/mock/')
    elif (m['model_id'], m['endpoint'], m['credential_env'], m['route']) != ('deterministic-mock-v1', None, None, 'mock'):
        raise ValueError('Mock configuration must explicitly identify the mock model and route')
    if m['backend'] == 'mock' and (m['max_requests_per_invocation'] is not None or m['min_request_interval_seconds'] != 0):
        raise ValueError('Mock backend does not use API request quotas or pacing')
    return c


def load_config(path):
    try:
        c = yaml.safe_load(relative_path(path).read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError):
        raise ValueError('Cannot read configuration YAML') from None
    return validate_config(c)


def software_versions():
    return {'python': platform.python_version(), **{p: version(p) for p in ('PyYAML', 'httpx', 'python-dotenv')}}


def source_identity(selector_file):
    paths = set((ROOT / 'src').rglob('*.py')) | set(selector_file.parent.rglob('*.py'))
    return {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name: file_digest(p)
            for p in sorted(paths) if '__pycache__' not in p.parts}


def prepare(c):
    synthetic = c['data_kind'] == 'synthetic'
    demos = load_records(relative_path(c['demo_path']), True, synthetic)
    questions = load_records(relative_path(c['dev_path']), False, synthetic)
    if {d['id'] for d in demos} & {q['id'] for q in questions}:
        raise ValueError('Demonstration and development IDs must be disjoint')
    if len(demos) != 20 or len(questions) != 10:
        raise ValueError('Pilot boundary requires exactly 20 demos and 10 development questions')
    selector, selector_file = import_selector(c['selector'])
    pool = {d['id']: d for d in demos}
    plan = []
    for q in questions:
        for strategy in c['strategies']:
            try:
                # Copies prevent selector mutation and query gold leakage. Seed is fixed,
                # selection occurs once per query/strategy, outside the condition loop.
                ids = selector(selector_query(q), deepcopy(demos), c['shot_count'], strategy, c['seed'])
            except Exception:
                raise ValueError('Selector failed; check Rayyan’s adapter, Urdu query contract and dependencies') from None
            selected = resolve_ids(ids, pool, c['shot_count'])
            for condition in c['conditions']:
                prompt = build_prompt(q, selected, condition)
                item = {'question_id': q['id'], 'strategy': strategy, 'condition': condition,
                        'shot_count': c['shot_count'], 'seed': c['seed'], 'demo_ids': ids.copy(),
                        'prompt': prompt, 'prompt_hash': digest(prompt)}
                plan.append(item)
    identity_config = {k: v for k, v in c.items() if k not in ('output_path', 'verification_receipt')}
    identity = {'configuration': identity_config, 'data': {k: file_digest(relative_path(c[k])) for k in ('demo_path', 'dev_path')},
                'sources': source_identity(selector_file), 'software': software_versions(),
                'template_version': TEMPLATE_VERSION, 'runner_version': RUNNER_VERSION,
                'plan_hash': digest(plan)}
    run_id = digest(identity)
    for item in plan:
        item['record_id'] = digest({'run_id': run_id, **item})
    return {'run_id': run_id, 'identity': identity, 'resolved_configuration': c,
            'created_at': now(), 'expected_records': len(plan), 'plan': plan,
            'mode': 'mock' if c['model']['backend'] == 'mock' else 'live', 'data_kind': c['data_kind']}


def append_json(path, value):
    with path.open('a', encoding='utf-8') as f:
        f.write(canonical(value) + '\n')
        f.flush()
        os.fsync(f.fileno())


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)


@contextmanager
def exclusive_output(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(path.suffix + '.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another process is writing this output') from None
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def read_journal(path, repair_tail=False):
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b'\n'):
        if not repair_tail:
            raise ValueError('Unterminated final JSONL line; inspect and use --resume --repair-tail to back up and recover')
        start = raw.rfind(b'\n') + 1
        try:
            json.loads(raw[start:])
            fixed = raw + b'\n'  # Preserve a complete valid final record.
        except (ValueError, UnicodeError):
            fixed = raw[:start]  # Only an invalid unterminated tail can be removed.
        backup = path.with_name(path.name + '.corrupt-' + str(time.time_ns()))
        backup.write_bytes(raw)
        with path.open('wb') as f:
            f.write(fixed)
            f.flush()
            os.fsync(f.fileno())
        raw = fixed
    rows = []
    for n, line in enumerate(raw.splitlines(), 1):
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError
            rows.append(row)
        except (ValueError, UnicodeError):
            raise ValueError(f'Corrupt JSONL line {n}; restore from backup or use a new output, no automatic interior repair') from None
    return rows


def validate_journal(rows, manifest):
    expected = {p['record_id']: p for p in manifest['plan']}
    successes = set()
    for row in rows:
        rid = row.get('record_id')
        if row.get('run_id') != manifest['run_id'] or rid not in expected or row.get('status') not in ('success', 'failure'):
            raise ValueError('Incompatible or malformed output record')
        item = expected[rid]
        if any(row.get(k) != v for k, v in item.items()):
            raise ValueError('Output identity or prompt was modified')
        if rid in successes:
            raise ValueError('Duplicate success or record after successful completion')
        if row['status'] == 'success':
            if not isinstance(row.get('raw_response'), str) or not row['raw_response'].strip():
                raise ValueError('Empty successful output record')
            successes.add(rid)
    return successes


def require_live_receipt(c):
    path = c['verification_receipt']
    if not path:
        raise ValueError('Live model verification receipt required; run configs/live_smoke.yaml first')
    try:
        receipt = json.loads(relative_path(path).read_text())
        journal = relative_path(receipt['output_path'])
        if receipt['model_hash'] != digest(c['model']) or receipt['output_hash'] != file_digest(journal):
            raise ValueError
        rows = read_journal(journal)
        if not all(any(r.get('record_id') == rid and r.get('status') == 'success' and r.get('mode') == 'live'
                       for r in rows) for rid in receipt['record_ids']):
            raise ValueError
        if len(receipt['record_ids']) != 4:
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError('Missing/incompatible live verification receipt; complete four-condition live synthetic smoke first') from None


def run(c, resume=False, question_limit=None, repair_tail=False, backend=None):
    validate_config(c)
    if question_limit is not None and (type(question_limit) is not int or not 1 <= question_limit <= 10):
        raise ValueError('question-limit must be 1..10')
    manifest = prepare(c)
    if c['data_kind'] == 'real':
        require_live_receipt(c)
    output = relative_path(c['output_path'])
    manifest_path = output.with_suffix('.manifest.json')
    with exclusive_output(output):
        if output.exists() or manifest_path.exists():
            if not resume:
                raise ValueError('Output/manifest already exists; use --resume or choose a new output')
            try:
                saved = json.loads(manifest_path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                raise ValueError('Missing/corrupt manifest; refuse to mix runs') from None
            if saved.get('run_id') != manifest['run_id'] or saved.get('identity') != manifest['identity'] or saved.get('plan') != manifest['plan']:
                raise ValueError('Incompatible run: configuration, data, selector, software, source or prompt changed; use a new output')
        else:
            atomic_json(manifest_path, manifest)
        rows = read_journal(output, repair_tail)
        done = validate_journal(rows, manifest)
        question_ids = list(dict.fromkeys(p['question_id'] for p in manifest['plan']))
        selected_questions = set(question_ids[:question_limit]) if question_limit else set(question_ids)
        pending = [p for p in manifest['plan'] if p['question_id'] in selected_questions and p['record_id'] not in done]
        if pending and backend is None:
            backend = (MockBackend() if c['model']['backend'] == 'mock' else
                       GoogleAIStudioBackend(c['model']) if c['model']['backend'] == 'google_ai_studio' else
                       OpenRouterBackend(c['model']))
        count, failed = 0, 0
        stop_reason = None
        for item in pending:
            if getattr(backend, 'requests_remaining', None) == 0:
                stop_reason = 'free_request_budget_exhausted'
                break
            record = {**item, 'run_id': manifest['run_id'], 'model_id': c['model']['model_id'],
                      'backend': c['model']['backend'], 'provider': c['model']['route'],
                      'inference_settings': c['model'], 'template_version': TEMPLATE_VERSION,
                      'configuration_hash': digest(manifest['identity']['configuration']),
                      'data_fingerprints': manifest['identity']['data'], 'timestamp': now(),
                      'mode': manifest['mode'], 'data_kind': c['data_kind']}
            start = time.monotonic()
            try:
                result, attempts = call_with_retries(backend, item['prompt'], c['model'])
                record.update(status='success', raw_response=result.text, request_id=result.request_id,
                              usage=result.usage, served_model=result.served_model,
                              served_provider=result.served_provider, finish_reason=result.finish_reason, attempts=attempts)
                count += 1
            except BackendError as exc:
                record.update(status='failure', error={'code': exc.code, 'transient': exc.transient},
                              attempts=exc.attempts)
                failed += 1
            except Exception:
                # Avoid persisting arbitrary plugin/client exception strings containing secrets.
                record.update(status='failure', error={'code': 'unexpected_backend_error', 'transient': False}, attempts=1)
                failed += 1
            if c['model']['backend'] == 'google_ai_studio':
                record['free_project_tier_confirmed_by_user'] = getattr(backend, 'free_tier_confirmed', False)
                record['model_access_metadata'] = getattr(backend, 'catalog_evidence', None)
            record['latency_seconds'] = round(time.monotonic() - start, 6)
            # Defense in depth for any known credential appearing in returned metadata.
            key = os.environ.get(c['model']['credential_env'] or '', '')
            if key:
                record = json.loads(canonical(record).replace(key, '[REDACTED]'))
            append_json(output, record)
            # Stop global auth/configuration errors; do not waste the remaining matrix calls.
            if record['status'] == 'failure' and record['error']['code'] in ('http_400', 'http_401', 'http_402', 'http_403', 'http_404', 'http_422', 'http_429', 'free_daily_quota_exhausted', 'free_catalog_preflight_failed', 'google_model_preflight_failed', 'google_daily_quota_exhausted', 'unexpected_nonzero_cost', 'free_policy_model_changed', 'free_request_budget_exhausted', 'retry_after_exceeds_wait_budget', 'provider_error_429', 'provider_error_400', 'provider_error_401', 'provider_error_402', 'provider_error_403', 'provider_error_404', 'provider_error_422'):
                break
        rows = read_journal(output)
        done = validate_journal(rows, manifest)
        # A live fixture smoke freezes model settings in an auditable secret-free receipt.
        if c['model']['backend'] != 'mock' and c['data_kind'] == 'synthetic':
            qid = question_ids[0]
            smoke = [p for p in manifest['plan'] if p['question_id'] == qid and p['strategy'] == c['strategies'][0]]
            if len(smoke) == 4 and all(p['record_id'] in done for p in smoke):
                atomic_json(output.parent / 'model_verification.json', {'verified_at': now(),
                            'model_hash': digest(c['model']), 'model': c['model'],
                            'output_path': c['output_path'], 'output_hash': file_digest(output),
                            'record_ids': [p['record_id'] for p in smoke]})
        summary = {'new_successes': count, 'new_failures': failed, 'total_successes': len(done),
                   'expected_records': len(manifest['plan']), 'output': c['output_path']}
        if c['model']['backend'] != 'mock':
            summary.update(requests_sent=getattr(backend, 'requests_sent', 0), stop_reason=stop_reason,
                           deferred_records=sum(p['record_id'] not in done for p in pending))
        return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['preview', 'run'])
    parser.add_argument('--config', default='configs/pilot.yaml')
    parser.add_argument('--output', help='Repository-relative output override')
    parser.add_argument('--question-limit', type=int)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--repair-tail', action='store_true')
    args = parser.parse_args(argv)
    load_dotenv(ROOT / '.env', override=False)
    try:
        c = load_config(args.config)
        if args.output:
            c['output_path'] = args.output
            validate_config(c)
        if args.repair_tail and not args.resume:
            raise ValueError('--repair-tail requires --resume')
        if args.question_limit is not None and not 1 <= args.question_limit <= 10:
            raise ValueError('question-limit must be 1..10')
        if args.action == 'preview':
            m = prepare(c)
            ids = list(dict.fromkeys(p['question_id'] for p in m['plan']))[:args.question_limit or 1]
            for p in m['plan']:
                if p['question_id'] in ids:
                    print(json.dumps({'mode': 'preview', 'data_kind': c['data_kind'], **p}, ensure_ascii=False))
            return 0
        summary = run(c, args.resume, args.question_limit, args.repair_tail)
        print(json.dumps(summary))
        return 1 if summary['new_failures'] else (3 if summary.get('deferred_records', 0) else 0)
    except (ValueError, OSError) as exc:
        # OSError may include local paths; never print arbitrary external exception text.
        print('Error: ' + (str(exc) if isinstance(exc, ValueError) else 'Local file operation failed'), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
