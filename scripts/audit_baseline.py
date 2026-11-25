"""Reconcile inherited runs, reproduce both parsers, and retain a record-level audit.

No inference, credentials or network calls. Original raw/manifest files and both bundled
score versions stay unchanged. New scoring is written only under results/verified/.
"""
import csv
from difflib import SequenceMatcher
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluation.answer_parser import PARSER_VERSION, parse_answer, normalize_text, to_decimal
from src.evaluation.report import build_report
from src.inference.runner import digest, load_config, prepare, validate_journal
from src.prompting.templates import build_prompt, build_zero_shot_prompt

EVIDENCE = ROOT / 'evidence/baseline_2026_11_25'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parser_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def inspect_manifest(folder, pool, dev):
    manifest = json.loads((folder / 'pilot_raw.manifest.json').read_text())
    raw = load(folder / 'pilot_raw.jsonl')
    identity, plan = manifest['identity'], manifest['plan']
    require(digest(identity) == manifest['run_id'], 'Manifest run identity hash mismatch')
    bare = [{k: v for k, v in p.items() if k != 'record_id'} for p in plan]
    require(digest(bare) == identity['plan_hash'], 'Manifest prompt-plan hash mismatch')
    require(len(plan) == manifest['expected_records'], 'Manifest count mismatch')
    config = identity['configuration']
    regenerated = prepare(manifest['resolved_configuration'])
    require([{k:v for k,v in p.items() if k != 'record_id'} for p in regenerated['plan']] == bare,
            'Current approved selector does not reproduce the archived plan')
    for name, p in [('demo_path', 'data/processed/demo_pool.jsonl'), ('dev_path', 'data/processed/dev.jsonl')]:
        require(identity['data'][name] == sha(ROOT / p), 'Frozen input changed')
    for p, item in zip(plan, bare):
        require(p['record_id'] == digest({'run_id': manifest['run_id'], **item}), 'Record identity hash mismatch')
        require(digest(p['prompt']) == p['prompt_hash'], 'Prompt hash mismatch')
        require(p['question_id'] in dev, 'Unknown development question')
        require(len(p['demo_ids']) == p['shot_count'], 'Wrong number of examples')
        require(len(set(p['demo_ids'])) == len(p['demo_ids']), 'Repeated example')
        require(set(p['demo_ids']) <= pool.keys(), 'Unapproved example')
        # Rebuild from question text and approved demonstrations only, never dev gold/solutions.
        q = {k: dev[p['question_id']][k] for k in ('id', 'question_en', 'question_ur')}
        prompt = (build_zero_shot_prompt(q, p['condition']) if p['shot_count'] == 0 else
                  build_prompt(q, [pool[k] for k in p['demo_ids']], p['condition']))
        require(prompt == p['prompt'], 'Archived prompt differs from controlled language template')
    successes = validate_journal(raw, manifest)
    require(len(successes) == len(plan), 'Incomplete saved run')
    for row in raw:
        require(row['configuration_hash'] == digest(config), 'Record configuration hash mismatch')
        if row['status'] != 'success':
            continue
        model = config['model']
        require(row['served_model'] == model['model_id'], 'Served model mismatch')
        if model['backend'] == 'ollama':
            access = row['model_access_metadata']
            require(access['digest'] == model['model_digest'], 'Archived local digest mismatch')
            require(access['quantization_level'] == 'Q4_K_M', 'Unexpected quantization')
            require(row['usage']['total_tokens'] < model['decoding']['num_ctx'], 'Context saturation')
    return manifest, raw


def main():
    receipt = json.loads((EVIDENCE / 'source_receipt.json').read_text())
    for relative, expected in receipt.get('auxiliary', {}).items():
        require(sha(ROOT / relative) == expected, 'Auxiliary archived evidence changed: '+relative)
    require(sha(EVIDENCE / 'parser_v1.py') == receipt['parser_v1_sha256'], 'Legacy parser bytes changed')
    legacy = parser_module(EVIDENCE / 'parser_v1.py', 'baseline_legacy_parser')
    pool = {r['id']: r for r in load(ROOT / 'data/processed/demo_pool.jsonl')}
    dev = {r['id']: r for r in load(ROOT / 'data/processed/dev.jsonl')}
    excluded = {r['id'] for r in load(ROOT / 'data/review/excluded_demos.jsonl')}
    require(len(pool) == 18 and len(dev) == 10 and len(excluded) == 2, 'Wrong frozen dataset size')
    require(not (pool.keys() & dev.keys() or excluded & (pool.keys() | dev.keys())), 'Data overlap')
    require(all(r['verified'] is True for r in pool.values()), 'Unapproved candidate')
    out, changes, manifests = [], [], {}
    for name, entry in receipt['runs'].items():
        folder = ROOT / entry['repo_folder']
        for relative, expected in entry['files'].items():
            require(sha(folder / relative) == expected, f'Inherited artifact changed: {name}/{relative}')
        manifest, raw = inspect_manifest(folder, pool, dev)
        manifests[name] = manifest
        staging = ROOT / 'results/verified' / name
        scored = build_report(folder / 'pilot_raw.jsonl', ROOT / 'data/processed/dev.jsonl', staging,
                              manifest_path=folder / 'pilot_raw.manifest.json')
        require(scored['reconciliation']['complete'], f'Incomplete evaluation: {name}')
        before = {r['record_id']: r for r in load(folder / 'scored_before_parser_fix/pilot_evaluated.jsonl')}
        supplied = {r['record_id']: r for r in load(folder / 'pilot_evaluated.jsonl')}
        new = {r['record_id']: r for r in load(staging / 'pilot_evaluated.jsonl')}
        require(before.keys() == supplied.keys() == new.keys(), 'Before/after record IDs differ')
        gained = lost = newly_wrong = 0
        for rid, row in new.items():
            old = legacy.parse_answer(row['raw_response'])
            require((old.prediction, old.status, old.detail) ==
                    (before[rid]['prediction'], before[rid]['parse_status'], before[rid]['parse_detail']),
                    f'Legacy parse reproduction failed: {rid}')
            require(before[rid]['correct'] == (old.status == 'ok' and old.value == to_decimal(row['gold_answer'])),
                    'Legacy correctness differs')
            require(row == supplied[rid], f'New bounded parser changed bundled v2 scored bytes: {rid}')
            gain = row['correct'] and not before[rid]['correct']
            loss = before[rid]['correct'] and not row['correct']
            gained += gain
            lost += loss
            newly_wrong += before[rid]['parse_status'] != 'ok' and row['parse_status'] == 'ok' and not row['correct']
            if gain or loss or (row['prediction'], row['parse_status']) != (before[rid]['prediction'], before[rid]['parse_status']):
                text = normalize_text(row['raw_response']).replace('*', '')
                cause = ('generic restatement' if 'FINAL_ANSWER:' in text and before[rid]['parse_status'] == 'ambiguous'
                         else 'missing colon')
                changes.append({'run': name, 'record_id': rid, 'question_id': row['question_id'],
                                'condition': row['condition'], 'strategy': row['strategy'],
                                'old_status': before[rid]['parse_status'], 'old_prediction': before[rid]['prediction'],
                                'new_status': row['parse_status'], 'new_prediction': row['prediction'],
                                'gold': row['gold_answer'], 'gained': gain, 'lost': loss,
                                'cause': cause, 'response': row['raw_response'],
                                'working_review': '', 'reviewer': ''})
        out.append({'run': name, 'folder': entry['repo_folder'], 'run_id': manifest['run_id'],
                    'raw_sha256': sha(folder / 'pilot_raw.jsonl'),
                    'manifest_sha256': sha(folder / 'pilot_raw.manifest.json'),
                    'scored': len(new), 'correct_before': sum(r['correct'] for r in before.values()),
                    'correct_after': sum(r['correct'] for r in new.values()),
                    'parse_failures_before': sum(r['parse_status'] != 'ok' for r in before.values()),
                    'parse_failures_after': sum(r['parse_status'] != 'ok' for r in new.values()),
                    'gained': gained, 'lost': lost, 'newly_parsed_wrong': newly_wrong,
                    'failed_entries': sum(r['status'] == 'failure' for r in raw),
                    'cutoff_responses': sum(r.get('finish_reason') == 'length' for r in new.values()),
                    'maximum_total_tokens': max(r['usage']['total_tokens'] for r in new.values()),
                    'verified_evaluated_sha256': sha(staging / 'pilot_evaluated.jsonl')})
    reference = manifests['31b_two_shot']['plan']
    for name in ('4b_two_shot', '1b_two_shot'):
        require([{k: r[k] for k in ('question_id','strategy','condition','demo_ids','prompt')} for r in manifests[name]['plan']]
                == [{k: r[k] for k in ('question_id','strategy','condition','demo_ids','prompt')} for r in reference],
                'Two-shot prompts/examples differ between models')
    require([r['prompt'] for r in manifests['4b_zero_shot']['plan']] ==
            [r['prompt'] for r in manifests['1b_zero_shot']['plan']], 'Zero-shot model prompts differ')
    previews = []
    for config in sorted((ROOT / 'configs').glob('*.yaml')):
        prepared = prepare(load_config(str(config.relative_to(ROOT))))
        previews.append({'config': str(config.relative_to(ROOT)), 'planned_records': prepared['expected_records']})
    pairs = []
    norm = lambda s: ' '.join(unicodedata.normalize('NFKC', s).casefold().split())
    for q in dev.values():
        for d in pool.values():
            ratio = SequenceMatcher(None, norm(q['question_en']), norm(d['question_en'])).ratio()
            pairs.append({'dev_id': q['id'], 'demo_id': d['id'], 'text_similarity': round(ratio, 4)})
    result = {'date': '2026-11-25', 'parser_version': PARSER_VERSION,
              'runs': out, 'total_scored': sum(x['scored'] for x in out),
              'total_gained': sum(x['gained'] for x in out), 'total_lost': sum(x['lost'] for x in out),
              'newly_parsed_wrong': sum(x['newly_parsed_wrong'] for x in out),
              'two_shot_prompts_identical': True, 'zero_shot_prompts_identical': True,
              'configs_previewed': previews, 'closest_demo_dev_text_pairs': sorted(pairs, key=lambda x:-x['text_similarity'])[:5],
              'urdu_solutions_with_ascii_words': sum(bool(__import__('re').search('[A-Za-z]', r['reasoning_ur'])) for r in pool.values()),
              'note': 'Saved response verification and offline rescoring; inherited local inference not repeated. Text similarity is a duplicate-screening heuristic, not translation review.'}
    (EVIDENCE / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    with (EVIDENCE / 'parser_changes.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(changes[0]));writer.writeheader();writer.writerows(changes)
    print(json.dumps({k:result[k] for k in ('total_scored','total_gained','total_lost','newly_parsed_wrong','urdu_solutions_with_ascii_words')}, indent=2))
    for row in out:
        print(row['run'], row['correct_before'], '->', row['correct_after'], '/', row['scored'])


if __name__ == '__main__':
    main()
