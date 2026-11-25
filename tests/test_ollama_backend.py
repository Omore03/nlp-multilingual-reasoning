"""Protocol simulations for the local Ollama adapter. Never contacts a real Ollama server."""
from copy import deepcopy
import json

import httpx
import pytest

from src.inference import runner as r
from src.inference.backends import BackendError
from src.inference.ollama_backend import (OLLAMA_ENDPOINT, OLLAMA_TAGS_URL, OLLAMA_VERSION_URL,
                                          OllamaBackend)
from tests.test_pipeline import project  # noqa: F401  (fixture)

SMOKE = 'configs/ollama_gemma3_1b_smoke.yaml'
PILOT = 'configs/pilot_ollama_gemma3_1b.yaml'


def tags(model, digest=None):
    return {'models': [{'name': 'other:latest', 'digest': '0' * 64},
                       {'name': model['model_id'], 'digest': digest or model['model_digest'], 'size': 806067407,
                        'details': {'parent_model': 'simulated', 'format': 'gguf', 'family': 'gemma3',
                                    'parameter_size': '999.89M', 'quantization_level': 'Q4_K_M',
                                    'context_length': 32768}}]}


def chat(configured, **overrides):
    body = {'model': configured['model_id'], 'message': {'role': 'assistant', 'content': 'مکمل حل\nFINAL_ANSWER: 5'},
            'done': True, 'done_reason': 'stop', 'prompt_eval_count': 400, 'eval_count': 20}
    body.update(overrides)
    return body


def make_backend(model, handler=None, digest=None, seen=None):
    def dispatch(request):
        if seen is not None:
            seen.append((request.method, str(request.url)))
        if request.method == 'GET' and str(request.url) == OLLAMA_VERSION_URL:
            return httpx.Response(200, json={'version': '0.40.18-simulated'})
        if request.method == 'GET' and str(request.url) == OLLAMA_TAGS_URL:
            return httpx.Response(200, json=tags(model, digest))
        assert request.method == 'POST' and str(request.url) == OLLAMA_ENDPOINT
        return handler(request) if handler else httpx.Response(200, json=chat(model))
    return OllamaBackend(model, client=httpx.Client(transport=httpx.MockTransport(dispatch)))


def test_payload_overrides_defaults_and_parses_response(project):
    model = r.load_config(SMOKE)['model']
    def handler(request):
        body = json.loads(request.content)
        assert body == {'model': 'gemma3:1b', 'messages': [{'role': 'user', 'content': 'اردو سوال'}],
                        'stream': False, 'options': {'temperature': 0, 'top_p': 1, 'seed': 42,
                                                     'num_predict': 2048, 'num_ctx': 4096}}
        assert 'authorization' not in request.headers
        return httpx.Response(200, json=chat(model))
    backend = make_backend(model, handler)
    result = backend.generate('اردو سوال', model)
    assert result.text == 'مکمل حل\nFINAL_ANSWER: 5'
    assert result.usage == {'prompt_tokens': 400, 'completion_tokens': 20, 'total_tokens': 420}
    assert result.served_model == 'gemma3:1b' and result.finish_reason == 'stop'
    assert backend.catalog_evidence['digest'] == model['model_digest']
    assert backend.catalog_evidence['ollama_version'] == '0.40.18-simulated'
    assert backend.catalog_evidence['quantization_level'] == 'Q4_K_M'


def test_preflight_runs_once(project):
    model = r.load_config(SMOKE)['model']
    seen = []
    backend = make_backend(model, seen=seen)
    backend.generate('a', model)
    backend.generate('b', model)
    assert [m for m, _ in seen].count('GET') == 2 and backend.requests_sent == 2


@pytest.mark.parametrize('digest', ['f' * 64])
def test_digest_mismatch_fails_closed_before_generation(project, digest):
    model = r.load_config(SMOKE)['model']
    backend = make_backend(model, lambda _: pytest.fail('No generation after failed preflight'), digest=digest)
    with pytest.raises(BackendError) as exc:
        backend.generate('a', model)
    assert exc.value.code == 'ollama_model_preflight_failed' and backend.requests_sent == 0


@pytest.mark.parametrize('overrides, code', [
    ({'done_reason': 'load'}, 'incomplete_response'),
    ({'done': False}, 'incomplete_response'),
    ({'model': 'gemma3:4b'}, 'served_model_mismatch'),
    ({'prompt_eval_count': 4000, 'eval_count': 96}, 'context_window_exceeded'),
    ({'eval_count': None}, 'missing_token_counts'),
])
def test_unusable_responses_are_rejected(project, overrides, code):
    model = r.load_config(SMOKE)['model']
    backend = make_backend(model, lambda _: httpx.Response(200, json=chat(model, **overrides)))
    with pytest.raises(BackendError) as exc:
        backend.generate('a', model)
    assert exc.value.code == code and not exc.value.transient


def test_max_token_cutoff_is_kept_as_the_models_answer(project):
    model = r.load_config(SMOKE)['model']
    looping = chat(model, done_reason='length', eval_count=2048,
                   message={'role': 'assistant', 'content': 'دوبارہ ' * 50})
    result = make_backend(model, lambda _: httpx.Response(200, json=looping)).generate('a', model)
    assert result.finish_reason == 'length' and result.usage['completion_tokens'] == 2048
    assert 'FINAL_ANSWER' not in result.text


def test_unreachable_server_is_terminal(project):
    model = r.load_config(SMOKE)['model']
    def dispatch(request):
        raise httpx.ConnectError('refused', request=request)
    backend = OllamaBackend(model, client=httpx.Client(transport=httpx.MockTransport(dispatch)))
    with pytest.raises(BackendError) as exc:
        backend.generate('a', model)
    assert exc.value.code == 'ollama_server_unreachable' and not exc.value.transient


def test_changed_settings_are_refused(project):
    model = r.load_config(SMOKE)['model']
    backend = make_backend(model)
    changed = deepcopy(model)
    changed['decoding']['temperature'] = 1
    with pytest.raises(BackendError) as exc:
        backend.generate('a', changed)
    assert exc.value.code == 'model_settings_changed'


@pytest.mark.parametrize('change', ['remote_endpoint', 'credential', 'short_digest', 'quota', 'pacing',
                                    'missing_num_ctx', 'small_ctx', 'missing_digest', 'paid'])
def test_config_validation(project, change):
    c = r.load_config(SMOKE)
    m = c['model']
    if change == 'remote_endpoint': m['endpoint'] = 'http://example.com:11434/api/chat'
    if change == 'credential': m['credential_env'] = 'OLLAMA_KEY'
    if change == 'short_digest': m['model_digest'] = '97558784bdc9'
    if change == 'quota': m['max_requests_per_invocation'] = 40
    if change == 'pacing': m['min_request_interval_seconds'] = 3.1
    if change == 'missing_num_ctx': del m['decoding']['num_ctx']
    if change == 'small_ctx': m['decoding']['num_ctx'] = 2048
    if change == 'missing_digest': del m['model_digest']
    if change == 'paid': m['free_only'] = False
    with pytest.raises(ValueError):
        r.validate_config(c)


@pytest.mark.parametrize('path, ok', [('results/pilot_raw.jsonl', True), ('results/gemma3_1b/pilot_raw.jsonl', True),
                                      ('results/a/b/pilot_raw.jsonl', False), ('results/gemma3_1b/other.jsonl', False),
                                      ('results/mock/../pilot_raw.jsonl', False)])
def test_real_output_paths(project, path, ok):
    c = r.load_config(PILOT)
    c['output_path'] = path
    if ok:
        r.validate_config(c)
    else:
        with pytest.raises(ValueError):
            r.validate_config(c)


def test_smoke_writes_receipt_with_local_metadata_and_resumes(project):
    root, _ = project
    c = r.load_config(SMOKE)
    first = r.run(c, question_limit=1, backend=make_backend(c['model']))
    assert first['new_successes'] == 4 and first['new_failures'] == 0 and first['requests_sent'] == 4
    rows = [json.loads(s) for s in (root / c['output_path']).read_text().splitlines()]
    assert all(row['backend'] == 'ollama' and row['provider'] == 'ollama-local' and row['mode'] == 'live'
               and row['model_access_metadata']['digest'] == c['model']['model_digest']
               and 'free_project_tier_confirmed_by_user' not in row for row in rows)
    pilot = r.load_config(PILOT)
    r.require_live_receipt(pilot)  # Same model block as the smoke, so the receipt is accepted.
    again = r.run(c, question_limit=1, resume=True,
                  backend=make_backend(c['model'], lambda _: pytest.fail('No calls after completion')))
    assert again['new_successes'] == 0


def test_unreachable_server_writes_one_failure_and_stops(project):
    root, _ = project
    c = r.load_config(SMOKE)
    def dispatch(request):
        raise httpx.ConnectError('refused', request=request)
    backend = OllamaBackend(c['model'], client=httpx.Client(transport=httpx.MockTransport(dispatch)))
    result = r.run(c, question_limit=1, backend=backend)
    assert result['new_failures'] == 1 and result['new_successes'] == 0
    row = json.loads((root / c['output_path']).read_text().splitlines()[0])
    assert row['error']['code'] == 'ollama_server_unreachable'


ZERO = 'configs/zeroshot_ollama_gemma3_1b.yaml'


def test_zero_shot_prompts_have_no_demonstrations_or_gold(project):
    from src.prompting.templates import ZERO_SHOT_CONDITIONS, build_zero_shot_prompt, LABELS
    q = {'id': 'q', 'question_en': 'EN target 7 + 8?', 'question_ur': 'اردو سوال 7 + 8؟', 'answer': 'SECRET_GOLD'}
    for condition in ZERO_SHOT_CONDITIONS:
        p = build_zero_shot_prompt(q, condition)
        assert 'SECRET_GOLD' not in p and 'FINAL_ANSWER:' in p
        assert LABELS['en'][0] not in p and LABELS['ur'][0] not in p  # no "Demonstration"/"مثال" blocks
        assert 'demonstrations' not in p and 'مثالوں' not in p
    assert build_zero_shot_prompt(q, 'U-U-U').count('اردو سوال') == 1
    assert 'EN target' in build_zero_shot_prompt(q, 'E-E-E')
    with pytest.raises(ValueError):
        build_zero_shot_prompt(q, 'U-E-E')


def test_zero_shot_plan_and_config_rules(project):
    root, _ = project
    import shutil
    from tests.test_pipeline import REPO
    for folder in ('data',):
        shutil.copytree(REPO / folder, root / folder)
    c = r.load_config(ZERO)
    plan = r.prepare(c)['plan']
    assert len(plan) == 30 and all(p['demo_ids'] == [] and p['shot_count'] == 0 and p['strategy'] == 'none' for p in plan)
    for change in ('selector', 'strategy', 'condition', 'shots'):
        bad = deepcopy(c)
        if change == 'selector': bad['selector'] = 'src.selection.pilot_adapter:select_examples'
        if change == 'strategy': bad['strategies'] = ['random']
        if change == 'condition': bad['conditions'] = ['U-U-U', 'U-U-E', 'U-E-E', 'E-E-E']
        if change == 'shots': bad['shot_count'] = 1
        with pytest.raises(ValueError):
            r.validate_config(bad)


def test_error_breakdown_categories_agree_with_exact_match(tmp_path):
    import importlib.util
    from tests.test_pipeline import REPO
    spec = importlib.util.spec_from_file_location('error_breakdown', REPO / 'scripts/error_breakdown.py')
    eb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(eb)
    base = {'strategy': 'random', 'condition': 'U-U-U', 'usage': {'completion_tokens': 200}, 'finish_reason': 'stop',
            'gold_answer': '1'}
    recs = [dict(base, correct=True, parse_status='ok', raw_response='حل ' * 30),
            dict(base, correct=True, parse_status='ok', finish_reason='length', raw_response='حل ' * 30),
            dict(base, correct=False, parse_status='ok', raw_response='The answer is', usage={'completion_tokens': 12}),
            dict(base, correct=False, parse_status='missing', finish_reason='length', raw_response='دوبارہ ' * 9),
            dict(base, correct=False, parse_status='missing', raw_response='کوئی نشان نہیں'),
            dict(base, correct=False, parse_status='ambiguous', raw_response='FINAL_ANSWER: 1 FINAL_ANSWER: 2')]
    path = tmp_path / 'e.jsonl'
    path.write_text('\n'.join(json.dumps(x, ensure_ascii=False) for x in recs))
    row = next(r for r in eb.breakdown(path) if (r['strategy'], r['condition']) == ('ALL', 'ALL'))
    assert (row['correct'], row['wrong_answer'], row['cut_off'], row['no_marker'], row['ambiguous']) == (2, 1, 1, 1, 1)
    assert row['format_failures'] == 3 and row['answer_only'] == 1
    assert row['off_language'] == 1  # the English 'The answer is' reply to an Urdu question
    assert row['lenient_correct'] == 2  # last literal marker in the ambiguous reply says 2, gold is 1
    assert eb.response_script('FINAL_ANSWER: 5') == 'none'


def test_lenient_diagnostic_reads_only_the_last_literal_marker():
    import importlib.util
    from tests.test_pipeline import REPO
    spec = importlib.util.spec_from_file_location('error_breakdown', REPO / 'scripts/error_breakdown.py')
    eb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(eb)
    assert str(eb.lenient_prediction('steps\nFINAL_ANSWER 70')) == '70'
    assert str(eb.lenient_prediction('final answer:\nQuestion: 10 floors\nFINAL_ANSWER: 90')) == '90'
    assert str(eb.lenient_prediction('FINAL_ANSWER: 3\nFINAL_ANSWER: ۲۱۶')) == '216'
    assert eb.lenient_prediction('70 FINAL_ANSWER') is None
    assert eb.lenient_prediction('final answer: 5') is None  # generic phrase is not the literal marker


def test_random_only_seed_check_config_is_accepted_and_similarity_only_is_not(project):
    root, _ = project
    c = r.load_config('configs/seedcheck_ollama_gemma3_4b_seed43.yaml')
    assert c['strategies'] == ['random'] and c['seed'] == 43 and c['model']['decoding']['seed'] == 42
    bad = deepcopy(c)
    bad['strategies'] = ['similarity']
    with pytest.raises(ValueError):
        r.validate_config(bad)
    bad = deepcopy(c)
    bad['conditions'] = ['U-U-U', 'E-E-E']
    with pytest.raises(ValueError):
        r.validate_config(bad)
