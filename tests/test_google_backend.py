"""Protocol simulations only. Never contacts Google or requires a real credential."""
from copy import deepcopy
import json

import httpx
import pytest

from src.inference import runner as r
from src.inference.backends import BackendError, call_with_retries
from src.inference.free_policy import GOOGLE_ENDPOINT, GOOGLE_MODEL_URL, GOOGLE_FREE_TIER_ENV
from src.inference.google_backend import GoogleAIStudioBackend
from tests.test_pipeline import project


def metadata():
    return {'name': 'models/gemma-4-31b-it', 'version': 'simulated-version',
            'inputTokenLimit': 262144, 'outputTokenLimit': 32768,
            'supportedGenerationMethods': ['generateContent', 'countTokens']}


def completion():
    return {'responseId': 'simulated-response', 'modelVersion': 'gemma-4-31b-it-simulated',
            'candidates': [{'content': {'parts': [{'thought': True, 'text': 'PRIVATE SIMULATED THOUGHT'},
                                                {'text': 'مکمل حل\n'}, {'text': 'FINAL_ANSWER: 5'}]},
                            'finishReason': 'STOP'}],
            'usageMetadata': {'promptTokenCount': 80, 'candidatesTokenCount': 12,
                              'totalTokenCount': 92, 'thoughtsTokenCount': 0}}


def make_backend(model, handler, monkeypatch, catalog=None, **kwargs):
    monkeypatch.setenv('GOOGLE_API_KEY', 'google-test-secret')
    monkeypatch.setenv(GOOGLE_FREE_TIER_ENV, 'true')
    def dispatch(request):
        assert request.headers['x-goog-api-key'] == 'google-test-secret'
        assert not request.url.params
        if request.method == 'GET':
            assert str(request.url) == GOOGLE_MODEL_URL
            return httpx.Response(200, json=catalog if catalog is not None else metadata())
        assert str(request.url) == GOOGLE_ENDPOINT
        return handler(request)
    client = httpx.Client(transport=httpx.MockTransport(dispatch))
    return GoogleAIStudioBackend(model, client=client, **kwargs)


def test_native_payload_visible_response_and_usage(project, monkeypatch):
    _, _ = project
    model = r.load_config('configs/live_smoke.yaml')['model']
    def handler(request):
        body = json.loads(request.content)
        assert set(body) == {'contents', 'generationConfig'}
        assert body['contents'] == [{'role': 'user', 'parts': [{'text': 'اردو سوال'}]}]
        assert body['generationConfig'] == {'temperature': 0, 'topP': 1, 'maxOutputTokens': 2048,
                                            'seed': 42, 'candidateCount': 1,
                                            'thinkingConfig': {'thinkingLevel': 'minimal'}}
        return httpx.Response(200, json=completion())
    backend = make_backend(model, handler, monkeypatch)
    result = backend.generate('اردو سوال', model)
    assert result.text == 'مکمل حل\nFINAL_ANSWER: 5'
    assert 'PRIVATE' not in result.text
    assert result.usage == {'prompt_tokens': 80, 'completion_tokens': 12, 'total_tokens': 92, 'reasoning_tokens': 0}
    assert 'cost' not in result.usage
    assert result.request_id == 'simulated-response'
    assert backend.requests_sent == 1


@pytest.mark.parametrize('change', ['paid_model', 'wrong_endpoint', 'wrong_credential', 'thinking', 'free_policy'])
def test_direct_config_rejects_policy_changes(project, change):
    _, _ = project
    c = r.load_config('configs/live_smoke.yaml')
    if change == 'paid_model': c['model']['model_id'] = 'gemini-4-carbon'
    if change == 'wrong_endpoint': c['model']['endpoint'] = 'https://openrouter.ai/api/v1/chat/completions'
    if change == 'wrong_credential': c['model']['credential_env'] = 'OPENROUTER_API_KEY'
    if change == 'thinking': c['model']['decoding']['thinking_level'] = 'high'
    if change == 'free_policy': c['model']['free_only'] = False
    with pytest.raises(ValueError):
        r.validate_config(c)


def test_key_and_project_confirmation_are_required_before_network(project, monkeypatch):
    _, _ = project
    model = r.load_config('configs/live_smoke.yaml')['model']
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    monkeypatch.delenv(GOOGLE_FREE_TIER_ENV, raising=False)
    with pytest.raises(ValueError, match='Set GOOGLE_API_KEY'):
        GoogleAIStudioBackend(model)
    monkeypatch.setenv('GOOGLE_API_KEY', 'google-test-secret')
    with pytest.raises(ValueError, match='Free tier with billing disabled'):
        GoogleAIStudioBackend(model)


@pytest.mark.parametrize('change', ['wrong_model', 'output_limit', 'no_generation', 'malformed'])
def test_native_metadata_preflight_fail_closed(project, monkeypatch, change):
    _, _ = project
    model = r.load_config('configs/live_smoke.yaml')['model']
    data = metadata()
    if change == 'wrong_model': data['name'] = 'models/gemini-other'
    if change == 'output_limit': data['outputTokenLimit'] = 10
    if change == 'no_generation': data['supportedGenerationMethods'] = ['countTokens']
    if change == 'malformed': data = {}
    backend = make_backend(model, lambda _: pytest.fail('No POST after incompatible metadata'), monkeypatch, catalog=data)
    with pytest.raises(BackendError, match='google_model_preflight_failed'):
        backend.generate('p', model)
    assert backend.requests_sent == 0


@pytest.mark.parametrize('status,transient', [(400, False), (401, False), (402, False), (403, False), (404, False), (429, True), (503, True)])
def test_native_http_errors_are_sanitized(project, monkeypatch, status, transient):
    _, _ = project
    model = r.load_config('configs/live_smoke.yaml')['model']
    body = {'error': {'message': 'google-test-secret must never be logged',
                      'details': [{'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '1.5s'}]}}
    backend = make_backend(model, lambda _: httpx.Response(status, json=body), monkeypatch)
    with pytest.raises(BackendError) as exc:
        backend.generate('p', model)
    assert str(exc.value) == f'http_{status}'
    assert exc.value.transient == transient and exc.value.retry_after == 1.5


@pytest.mark.parametrize('change,code', [('blocked', 'google_prompt_blocked'), ('empty', 'empty_response'),
                                       ('truncated', 'incomplete_response'), ('malformed', 'malformed_provider_response')])
def test_native_completion_boundaries(project, monkeypatch, change, code):
    _, _ = project
    model = r.load_config('configs/live_smoke.yaml')['model']
    body = completion()
    if change == 'blocked': body = {'promptFeedback': {'blockReason': 'SAFETY'}}
    if change == 'empty': body['candidates'][0]['content']['parts'] = [{'text': ' '}]
    if change == 'truncated': body['candidates'][0]['finishReason'] = 'MAX_TOKENS'
    if change == 'malformed': body = {'candidates': []}
    backend = make_backend(model, lambda _: httpx.Response(200, json=body), monkeypatch)
    with pytest.raises(BackendError, match=code):
        backend.generate('p', model)


def test_google_daily_quota_stops_without_retry(project, monkeypatch):
    root, _ = project
    c = r.load_config('configs/live_smoke.yaml')
    body = {'error': {'details': [{'@type': 'type.googleapis.com/google.rpc.QuotaFailure',
            'violations': [{'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier'}]}]}}
    backend = make_backend(c['model'], lambda _: httpx.Response(429, json=body), monkeypatch,
                           sleep=lambda _: pytest.fail('No retry after daily exhaustion'))
    result = r.run(c, question_limit=1, backend=backend)
    assert result['new_failures'] == 1 and backend.requests_sent == 1
    row = json.loads((root / c['output_path']).read_text().splitlines()[0])
    assert row['error']['code'] == 'google_daily_quota_exhausted'


def test_direct_smoke_receipt_metadata_and_resume(project, monkeypatch):
    root, _ = project
    c = r.load_config('configs/live_smoke.yaml')
    c['model']['max_requests_per_invocation'] = 2
    clock, waits = [0.0], []
    def sleep(seconds):
        waits.append(seconds)
        clock[0] += seconds
    def handler(_):
        body = completion()
        body['responseId'] = 'simulated-google-test-secret'
        return httpx.Response(200, json=body)
    backend = make_backend(c['model'], handler, monkeypatch, sleep=sleep, monotonic=lambda: clock[0])
    first = r.run(c, question_limit=1, backend=backend)
    assert first['total_successes'] == 2 and first['deferred_records'] == 2 and waits == [3.1]
    backend = make_backend(c['model'], handler, monkeypatch, sleep=lambda _: None)
    second = r.run(c, question_limit=1, resume=True, backend=backend)
    assert second['new_successes'] == 2 and second['total_successes'] == 4
    output = root / c['output_path']
    assert b'google-test-secret' not in output.read_bytes()
    rows = [json.loads(s) for s in output.read_text().splitlines()]
    assert all(row['free_project_tier_confirmed_by_user'] and row['model_access_metadata']['version'] == 'simulated-version'
               for row in rows)
    pilot = deepcopy(c)
    pilot['verification_receipt'] = 'results/live_smoke/google_direct/model_verification.json'
    r.require_live_receipt(pilot)
    assert r.run(c, question_limit=1, resume=True)['new_successes'] == 0
