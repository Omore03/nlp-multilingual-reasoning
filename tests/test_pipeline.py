from copy import deepcopy
import json
from pathlib import Path
import shutil

import httpx
import pytest

from src.inference import runner as r
from src.inference.backends import (BackendError, Completion, MockBackend, OpenRouterBackend,
                                    call_with_retries, retry_delay)
from src.inference.contracts import load_records, resolve_ids, selector_query
from src.prompting.templates import CONDITIONS, FINAL_MARKER, LABELS, TEMPLATE_VERSION, build_prompt

REPO = Path(__file__).resolve().parents[1]


def free_catalog():
    from src.inference.free_policy import FREE_MODEL_ID, FREE_ROUTE
    return {'data': {'id': FREE_MODEL_ID, 'endpoints': [{
        'tag': FREE_ROUTE, 'pricing': {'prompt': '0', 'completion': '0'},
        'supported_parameters': ['temperature', 'top_p', 'max_tokens', 'seed', 'reasoning'],
        'context_length': 262144, 'max_completion_tokens': 32768}]}}


def free_client(handler):
    def dispatch(request):
        if request.method == 'GET':
            return httpx.Response(200, json=free_catalog())
        return handler(request)
    return httpx.Client(transport=httpx.MockTransport(dispatch))


@pytest.fixture
def project(tmp_path, monkeypatch):
    for folder in ('configs', 'src', 'tests/fixtures'):
        shutil.copytree(REPO / folder, tmp_path / folder)
    monkeypatch.setattr(r, 'ROOT', tmp_path)
    return tmp_path, r.load_config('configs/mock.yaml')


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def prompt_data():
    demos = [dict(id=f'd{i}', question_en=f'EN demo {i}', question_ur=f'اردو مثال {i}',
                  reasoning_en=f'EN full steps {i}', reasoning_ur=f'اردو مکمل حل {i}', answer=str(i+11)) for i in (1, 2)]
    q = dict(id='q', question_en='EN target 7 + 8?', question_ur='اردو سوال 7 + 8؟', answer='SECRET_GOLD_SENTINEL')
    return q, demos


@pytest.mark.parametrize('condition', list(CONDITIONS))
def test_prompt_languages_complete_order_and_no_gold(condition):
    q, demos = prompt_data()
    ql, dl, il = CONDITIONS[condition]
    p = build_prompt(q, demos, condition)
    assert q['question_' + ql] in p
    assert q['question_' + ('en' if ql == 'ur' else 'ur')] not in p
    positions = []
    for d in demos:
        assert d['question_' + dl] in p and d['reasoning_' + dl] in p
        assert d['question_' + ('en' if dl == 'ur' else 'ur')] not in p
        positions.append(p.index(d['question_' + dl]))
    assert positions == sorted(positions)
    assert p.count(FINAL_MARKER) == 3  # One convention instruction and two demonstration answers.
    assert p.count(LABELS[il][2] + ':') == 2
    assert p.splitlines().count(LABELS[il][3]) == 1
    assert 'SECRET_GOLD_SENTINEL' not in p
    assert p == build_prompt({**q, 'answer': 'DIFFERENT_GOLD'}, demos, condition)
    assert p.encode('utf-8').decode('utf-8') == p


@pytest.mark.parametrize('ids', [['x', 'd1'], ['d1', 'd1'], ['d1'], [1, 2], ('d1', 'd2')])
def test_reject_invalid_selector_ids(ids):
    with pytest.raises(ValueError):
        resolve_ids(ids, {'d1': {}, 'd2': {}}, 2)


def test_resolve_preserves_order():
    assert resolve_ids(['b', 'a'], {'a': {'id': 'a'}, 'b': {'id': 'b'}}, 2) == [{'id': 'b'}, {'id': 'a'}]


def test_selector_boundary_has_only_urdu_and_id():
    q, _ = prompt_data()
    assert selector_query(q) == {'id': 'q', 'question_ur': q['question_ur']}


def test_once_per_question_strategy_and_shared_ids(project, monkeypatch):
    root, c = project
    calls = []
    def selector(query, pool, k, strategy, seed):
        calls.append((query, strategy, seed))
        assert set(query) == {'id', 'question_ur'}
        return ['synthetic-demo-02', 'synthetic-demo-01']
    monkeypatch.setattr(r, 'import_selector', lambda _: (selector, root / 'tests/fixtures/selector.py'))
    m = r.prepare(c)
    assert len(calls) == 20 and all(x[2] == 42 for x in calls)
    assert len(m['plan']) == 80
    assert all(p['demo_ids'] == ['synthetic-demo-02', 'synthetic-demo-01'] for p in m['plan'])


def test_full_matrix_metadata_utf8_and_resume(project):
    root, c = project
    s = r.run(c)
    assert s == dict(new_successes=80, new_failures=0, total_successes=80, expected_records=80, output=c['output_path'])
    out = root / c['output_path']
    before = out.read_bytes()
    rows = read(out)
    assert len(rows) == len({x['record_id'] for x in rows}) == 80
    assert len({(x['question_id'], x['strategy'], x['condition']) for x in rows}) == 80
    required = {'question_id', 'condition', 'strategy', 'shot_count', 'seed', 'model_id', 'demo_ids', 'prompt', 'raw_response',
                'run_id', 'record_id', 'backend', 'inference_settings', 'template_version', 'configuration_hash',
                'data_fingerprints', 'timestamp', 'request_id', 'usage', 'latency_seconds'}
    for row in rows:
        assert required <= row.keys()
        assert row['mode'] == 'mock' and row['data_kind'] == 'synthetic' and row['status'] == 'success'
        assert row['template_version'] == TEMPLATE_VERSION
        assert not {'prediction', 'gold_answer', 'correct', 'parse_status'} & row.keys()
    assert 'پنسلیں'.encode() in before
    assert r.run(c, resume=True)['new_successes'] == 0
    assert out.read_bytes() == before
    manifest = json.loads(out.with_suffix('.manifest.json').read_text())
    assert manifest['expected_records'] == 80 and manifest['identity']['software']['httpx']


def test_interrupted_subset_can_resume_full(project):
    root, c = project
    assert r.run(c, question_limit=1)['total_successes'] == 8
    assert r.run(c, resume=True)['new_successes'] == 72
    assert len(read(root / c['output_path'])) == 80


@pytest.mark.parametrize('change', ['seed', 'data', 'source', 'selector_version', 'decoding'])
def test_incompatible_runs_preserve_successes(project, change):
    root, c = project
    r.run(c, question_limit=1)
    output = root / c['output_path']
    before = output.read_bytes()
    if change == 'seed': c['seed'] += 1
    if change == 'selector_version': c['selector_version'] = 'new-encoder'
    if change == 'decoding': c['model']['decoding']['max_tokens'] += 1
    if change == 'data':
        path = root / c['dev_path']
        rows = read(path)
        rows[0]['question_ur'] += ' اضافی متن'
        path.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in rows))
    if change == 'source':
        path = root / 'src/prompting/templates.py'
        path.write_text(path.read_text() + '\n# revised\n')
    with pytest.raises(ValueError, match='Incompatible'):
        r.run(c, resume=True)
    assert output.read_bytes() == before


def test_missing_and_overlap_data(project):
    root, c = project
    path = root / c['dev_path']
    rows = read(path)
    rows[0]['id'] = 'synthetic-demo-01'
    path.write_text(''.join(json.dumps(x) + '\n' for x in rows))
    with pytest.raises(ValueError, match='disjoint'):
        r.prepare(c)
    del rows[0]['question_ur']
    path.write_text(''.join(json.dumps(x) + '\n' for x in rows))
    with pytest.raises(ValueError, match='required'):
        r.prepare(c)


def test_dev_optional_verified_and_fixture_honesty(project):
    root, c = project
    path = root / c['dev_path']
    assert 'verified' not in load_records(path, synthetic=True)[0]
    rows = read(path)
    rows[0]['verified'] = False
    path.write_text(''.join(json.dumps(x) + '\n' for x in rows))
    assert load_records(path, synthetic=True)[0]['verified'] is False
    rows[0]['verified'] = True
    path.write_text(''.join(json.dumps(x) + '\n' for x in rows))
    with pytest.raises(ValueError, match='human verification'):
        load_records(path, synthetic=True)


@pytest.mark.parametrize('field,value', [('shot_count', 4), ('conditions', ['bad']), ('conditions', ['E-E-E', 'E-E-E']),
                                        ('strategies', ['diversity']), ('seed', True)])
def test_bad_config(project, field, value):
    _, c = project
    c[field] = value
    with pytest.raises(ValueError):
        r.validate_config(c)


def test_missing_production_inputs_and_selector(project):
    root, _ = project
    c = r.load_config('configs/pilot.yaml')
    with pytest.raises(ValueError, match='Hussain'):
        r.prepare(c)
    from src.inference.contracts import import_selector
    with pytest.raises(ValueError, match='Rayyan'):
        import_selector('no_such_selector_module:select_examples')


def test_output_separation(project):
    _, c = project
    c['output_path'] = 'results/pilot_raw.jsonl'
    with pytest.raises(ValueError):
        r.validate_config(c)


class SequenceBackend:
    def __init__(self, values): self.values, self.calls = iter(values), 0
    def generate(self, prompt, model):
        self.calls += 1
        v = next(self.values)
        if isinstance(v, Exception): raise v
        return Completion(v)


def test_retry_and_terminal_and_empty(project):
    _, c = project
    waits = []
    backend = SequenceBackend([BackendError('http_429', True, 0.5), 'ok'])
    result, attempts = call_with_retries(backend, 'p', c['model'], waits.append)
    assert result.text == 'ok' and attempts == 2 and waits == [0.5]
    backend = SequenceBackend([BackendError('http_401')])
    with pytest.raises(BackendError) as exc:
        call_with_retries(backend, 'p', c['model'], waits.append)
    assert backend.calls == exc.value.attempts == 1
    backend = SequenceBackend(['', ' ', ''])
    with pytest.raises(BackendError, match='empty_response'):
        call_with_retries(backend, 'p', c['model'], lambda _: None)
    assert backend.calls == 3
    backend = SequenceBackend([BackendError('http_429', True, 999)])
    with pytest.raises(BackendError, match='wait_budget'):
        call_with_retries(backend, 'p', c['model'], lambda _: pytest.fail('must not sleep'))


def test_failure_retry_on_resume(project):
    root, c = project
    class FailOne(MockBackend):
        def __init__(self): self.first = True
        def generate(self, prompt, model):
            if self.first:
                self.first = False
                raise BackendError('test_terminal')
            return super().generate(prompt, model)
    assert r.run(c, backend=FailOne())['total_successes'] == 79
    s = r.run(c, resume=True)
    assert s['new_successes'] == 1 and s['total_successes'] == 80
    rows = read(root / c['output_path'])
    assert len(rows) == 81 and len({x['record_id'] for x in rows if x['status'] == 'success'}) == 80


def test_auth_failure_stops_matrix(project):
    root, c = project
    s = r.run(c, backend=SequenceBackend([BackendError('http_401')]))
    assert s['new_failures'] == 1
    assert len(read(root / c['output_path'])) == 1


def test_tail_repair_is_explicit_and_backs_up(project):
    root, c = project
    r.run(c, question_limit=1)
    out = root / c['output_path']
    original = out.read_bytes()
    with out.open('ab') as f: f.write(b'{"record_id":"unfinished')
    with pytest.raises(ValueError, match='Unterminated'):
        r.run(c, resume=True)
    assert r.run(c, resume=True, question_limit=1, repair_tail=True)['total_successes'] == 8
    assert out.read_bytes() == original
    assert len(list(out.parent.glob('*.corrupt-*'))) == 1


def test_valid_unterminated_tail_preserved_and_interior_corruption_rejected(project):
    root, c = project
    r.run(c, question_limit=1)
    out = root / c['output_path']
    original = out.read_bytes()
    out.write_bytes(original.rstrip(b'\n'))
    r.run(c, resume=True, repair_tail=True, question_limit=1)
    assert out.read_bytes() == original
    out.write_bytes(b'not-json\n' + original)
    with pytest.raises(ValueError, match='Corrupt JSONL line 1'):
        r.run(c, resume=True, repair_tail=True)


def test_duplicate_success_rejected(project):
    root, c = project
    r.run(c, question_limit=1)
    out = root / c['output_path']
    r.append_json(out, read(out)[0])
    with pytest.raises(ValueError, match='Duplicate'):
        r.run(c, resume=True)


def test_mock_is_deterministic():
    assert MockBackend().generate('اردو', {'model_id': 'mock'}) == MockBackend().generate('اردو', {'model_id': 'mock'})


def test_openrouter_payload_response_and_redaction(project, monkeypatch):
    _, _ = project
    c = r.load_config('configs/openrouter_live_smoke.yaml')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'secret-test-value')
    def handler(request):
        payload = json.loads(request.content)
        assert payload['provider'] == {'only': ['google-ai-studio'], 'allow_fallbacks': False, 'require_parameters': True,
                                       'max_price': {'prompt': 0, 'completion': 0, 'request': 0}}
        assert payload['temperature'] == 0 and payload['max_tokens'] == 2048
        assert 'enable_thinking' not in payload and payload['reasoning'] == {'enabled': False}
        return httpx.Response(200, json={'id': 'req-1', 'model': c['model']['model_id'], 'provider': 'Google AI Studio',
            'choices': [{'message': {'content': 'hello secret-test-value'}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 5, 'completion_tokens': 3, 'arbitrary_header': 'secret-test-value'}})
    backend = OpenRouterBackend(c['model'], free_client(handler))
    result = backend.generate('اردو', c['model'])
    assert result.text == 'hello [REDACTED]' and result.usage == {'prompt_tokens': 5, 'completion_tokens': 3}


@pytest.mark.parametrize('status,transient', [(400, False), (401, False), (403, False), (429, True), (503, True)])
def test_http_error_sanitization(project, monkeypatch, status, transient):
    _, _ = project
    c = r.load_config('configs/openrouter_live_smoke.yaml')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'secret-test-value')
    client = free_client(lambda _: httpx.Response(status, text='secret-test-value', headers={'Retry-After': '2'}))
    backend = OpenRouterBackend(c['model'], client, sleep=lambda _: None)
    with pytest.raises(BackendError) as exc:
        backend.generate('prompt', c['model'])
    assert exc.value.transient == transient and exc.value.retry_after == 2
    assert 'secret' not in str(exc.value)


def test_live_receipt_required(project):
    _, _ = project
    c = r.load_config('configs/pilot.yaml')
    with pytest.raises(ValueError, match='verification receipt'):
        r.require_live_receipt(c)


def test_preview_and_cli_validation(project, capsys):
    _, _ = project
    assert r.main(['preview', '--config', 'configs/mock.yaml', '--question-limit', '1']) == 0
    assert len(capsys.readouterr().out.splitlines()) == 8
    assert r.main(['run', '--config', 'configs/mock.yaml', '--question-limit', '0']) == 2
    assert r.main(['run', '--config', 'configs/mock.yaml', '--repair-tail']) == 2


def test_retry_after_http_date():
    assert retry_delay('Wed, 01 Jan 2020 00:00:00 GMT') == 0
    assert retry_delay('nonsense') is None


@pytest.mark.parametrize('body,code', [
    ({'choices': [{'message': {'content': ''}, 'finish_reason': 'stop'}]}, 'empty_response'),
    ({'choices': [{'message': {'content': 'partial'}, 'finish_reason': 'length'}]}, 'incomplete_response'),
    ({'choices': []}, 'malformed_provider_response'),
    ({'error': {'code': 401, 'message': 'secret-test-value'}}, 'provider_error_401'),
])
def test_provider_edge_responses(project, monkeypatch, body, code):
    _, _ = project
    c = r.load_config('configs/openrouter_live_smoke.yaml')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'secret-test-value')
    client = free_client(lambda _: httpx.Response(200, json=body))
    with pytest.raises(BackendError, match=code):
        OpenRouterBackend(c['model'], client, sleep=lambda _: None).generate('p', c['model'])


def test_live_smoke_receipt_offline_simulation(project, monkeypatch):
    root, _ = project
    c = r.load_config('configs/openrouter_live_smoke.yaml')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'secret-test-value')
    body = {'id': 'fake-request-secret-test-value', 'model': c['model']['model_id'], 'provider': 'Google AI Studio',
            'choices': [{'message': {'content': 'SIMULATED TEST OUTPUT'}, 'finish_reason': 'stop'}]}
    client = free_client(lambda _: httpx.Response(200, json=body))
    backend = OpenRouterBackend(c['model'], client, sleep=lambda _: None)
    assert r.run(c, question_limit=1, backend=backend)['total_successes'] == 4
    assert b'secret-test-value' not in (root / c['output_path']).read_bytes()
    pilot = deepcopy(c)
    pilot['verification_receipt'] = 'results/live_smoke/model_verification.json'
    r.require_live_receipt(pilot)
    pilot['model']['decoding']['temperature'] = 0.1
    with pytest.raises(ValueError, match='incompatible live verification'):
        r.require_live_receipt(pilot)


def test_bounded_retry_exhaustion(project):
    _, c = project
    backend = SequenceBackend([BackendError('http_503', True)] * 3)
    waits = []
    with pytest.raises(BackendError):
        call_with_retries(backend, 'p', c['model'], waits.append)
    assert backend.calls == 3 and waits == [1, 2]


def test_lock_rejects_concurrent_writer(project):
    root, c = project
    with r.exclusive_output(root / c['output_path']):
        with pytest.raises(ValueError, match='Another process'):
            r.run(c)


@pytest.mark.parametrize('change', ['paid_id', 'wrong_route', 'disabled_policy', 'unpaced', 'oversized_budget'])
def test_free_policy_rejects_unsafe_config(project, change):
    _, _ = project
    c = r.load_config('configs/openrouter_live_smoke.yaml')
    if change == 'paid_id': c['model']['model_id'] = 'google/gemma-4-31b-it'
    if change == 'wrong_route': c['model']['route'] = 'deepinfra/fp8'
    if change == 'disabled_policy': c['model']['free_only'] = False
    if change == 'unpaced': c['model']['min_request_interval_seconds'] = 0
    if change == 'oversized_budget': c['model']['max_requests_per_invocation'] = 50
    with pytest.raises(ValueError):
        r.validate_config(c)


def test_direct_backend_rejects_paid_model_before_network(project):
    _, _ = project
    c = r.load_config('configs/openrouter_live_smoke.yaml')
    c['model']['model_id'] = 'qwen/qwen3-235b-a22b-2507'
    with pytest.raises(ValueError, match='Zero-cost policy'):
        OpenRouterBackend(c['model'])


@pytest.mark.parametrize('change', ['price', 'request_fee', 'missing_price', 'missing_route', 'unsupported', 'malformed'])
def test_free_catalog_fail_closed_before_any_inference(project, monkeypatch, change):
    _, _ = project
    c = r.load_config('configs/openrouter_live_smoke.yaml')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'secret-test-value')
    body = free_catalog()
    endpoint = body['data']['endpoints'][0]
    if change == 'price': endpoint['pricing']['prompt'] = '0.000001'
    if change == 'request_fee': endpoint['pricing']['request'] = '0.01'
    if change == 'missing_price': del endpoint['pricing']['completion']
    if change == 'missing_route': endpoint['tag'] = 'other-provider'
    if change == 'unsupported': endpoint['supported_parameters'].remove('seed')
    if change == 'malformed': body = {}
    calls = []
    def handler(request):
        calls.append(request.method)
        return httpx.Response(200, json=body)
    backend = OpenRouterBackend(c['model'], httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(BackendError, match='free_catalog_preflight_failed'):
        backend.generate('p', c['model'])
    assert calls == ['GET']


def test_unexpected_reported_cost_stops_invocation(project, monkeypatch):
    root, _ = project
    c = r.load_config('configs/openrouter_live_smoke.yaml')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'secret-test-value')
    body = {'choices': [{'message': {'content': 'reply'}, 'finish_reason': 'stop'}], 'usage': {'cost': 0.01}}
    backend = OpenRouterBackend(c['model'], free_client(lambda _: httpx.Response(200, json=body)))
    summary = r.run(c, question_limit=1, backend=backend)
    assert summary['new_failures'] == 1 and backend.requests_sent == 1
    assert read(root / c['output_path'])[0]['error']['code'] == 'unexpected_nonzero_cost'
    assert not (root / 'results/live_smoke/model_verification.json').exists()


def test_free_budget_pacing_and_resume(project, monkeypatch):
    root, _ = project
    c = r.load_config('configs/openrouter_live_smoke.yaml')
    c['model']['max_requests_per_invocation'] = 2
    monkeypatch.setenv('OPENROUTER_API_KEY', 'secret-test-value')
    clock, waits, requests = [0.0], [], []
    def sleep(seconds):
        waits.append(seconds)
        clock[0] += seconds
    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={'model': c['model']['model_id'], 'provider': 'Google AI Studio',
            'choices': [{'message': {'content': 'SIMULATED FREE RESPONSE'}, 'finish_reason': 'stop'}],
            'usage': {'cost': 0}})
    backend = OpenRouterBackend(c['model'], free_client(handler), sleep=sleep, monotonic=lambda: clock[0])
    first = r.run(c, question_limit=1, backend=backend)
    assert first['total_successes'] == 2 and first['deferred_records'] == 2
    assert first['stop_reason'] == 'free_request_budget_exhausted' and first['new_failures'] == 0
    assert len(requests) == 2 and waits == [3.1]
    with pytest.raises(BackendError, match='free_request_budget_exhausted'):
        backend.generate('p', c['model'])
    resumed_backend = OpenRouterBackend(c['model'], free_client(handler), sleep=lambda _: None)
    second = r.run(c, question_limit=1, resume=True, backend=resumed_backend)
    assert second['new_successes'] == 2 and second['total_successes'] == 4
    assert len(read(root / c['output_path'])) == 4
    assert all(p['model'].endswith(':free') and p['provider']['max_price']['request'] == 0 for p in requests)


def test_daily_free_quota_exhaustion_no_retry_or_matrix_waste(project, monkeypatch):
    root, _ = project
    c = r.load_config('configs/openrouter_live_smoke.yaml')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'secret-test-value')
    client = free_client(lambda _: httpx.Response(429, headers={'X-RateLimit-Remaining': '0', 'X-RateLimit-Limit': '50'}))
    backend = OpenRouterBackend(c['model'], client, sleep=lambda _: pytest.fail('Do not retry exhausted daily quota'))
    summary = r.run(c, question_limit=1, backend=backend)
    assert summary['new_failures'] == 1 and backend.requests_sent == 1
    assert read(root / c['output_path'])[0]['error']['code'] == 'free_daily_quota_exhausted'
