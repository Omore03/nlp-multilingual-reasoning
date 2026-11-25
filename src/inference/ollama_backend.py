"""Local Ollama adapter for the small-model rerun (e.g. gemma3:1b) on the user's own machine.

Sends the same single user-turn prompt as the hosted adapters. Talks only to the local
Ollama server; no credentials, billing or remote fallback. The pulled model is pinned by
its full Ollama manifest digest so a silently re-pulled or different model cannot be used.
"""
from copy import deepcopy
import re
import time

import httpx

from src.inference.backends import BackendError, Completion

OLLAMA_BASE = 'http://127.0.0.1:11434'
OLLAMA_ENDPOINT = OLLAMA_BASE + '/api/chat'
OLLAMA_TAGS_URL = OLLAMA_BASE + '/api/tags'
OLLAMA_VERSION_URL = OLLAMA_BASE + '/api/version'
OLLAMA_ROUTE = 'ollama-local'
DIGEST = re.compile(r'[0-9a-f]{64}\Z')


def require_local_ollama_model(model):
    if (model.get('free_only') is not True or model.get('endpoint') != OLLAMA_ENDPOINT
            or model.get('route') != OLLAMA_ROUTE or model.get('credential_env') is not None
            or not isinstance(model.get('model_id'), str) or not model['model_id'].strip()
            or not isinstance(model.get('model_digest'), str) or not DIGEST.fullmatch(model['model_digest'])):
        raise ValueError('Ollama backend requires the local endpoint, route ollama-local, no credential, '
                         'a model_id and its full 64-hex model_digest from `ollama list`/api/tags')


def verify_local_model(tags, version, model):
    """Fail closed unless the configured tag is present with exactly the pinned digest."""
    try:
        entry = next(m for m in tags['models'] if m['name'] == model['model_id'])
        if entry['digest'] != model['model_digest']:
            raise ValueError
        details = entry.get('details', {})
        return {'ollama_version': version['version'], 'name': entry['name'], 'digest': entry['digest'],
                'size_bytes': entry.get('size'),
                **{k: details.get(k) for k in ('parent_model', 'format', 'family', 'parameter_size',
                                               'quantization_level', 'context_length')}}
    except (KeyError, TypeError, StopIteration, ValueError):
        raise BackendError('ollama_model_preflight_failed') from None


class OllamaBackend:
    def __init__(self, model, client=None):
        require_local_ollama_model(model)
        self.model = deepcopy(model)
        self.client = client or httpx.Client(timeout=model['timeout_seconds'], follow_redirects=False)
        self.requests_sent = 0
        self.catalog_evidence = None

    def preflight(self):
        try:
            version = self.client.get(OLLAMA_VERSION_URL)
            tags = self.client.get(OLLAMA_TAGS_URL)
        except (httpx.TimeoutException, httpx.NetworkError):
            raise BackendError('ollama_server_unreachable') from None
        except httpx.HTTPError:
            raise BackendError('transport_error') from None
        if version.status_code != 200 or tags.status_code != 200:
            raise BackendError('ollama_model_preflight_failed')
        try:
            self.catalog_evidence = verify_local_model(tags.json(), version.json(), self.model)
        except ValueError:
            raise BackendError('ollama_model_preflight_failed') from None

    def generate(self, prompt, model):
        if model != self.model:
            raise BackendError('model_settings_changed')
        if self.catalog_evidence is None:
            self.preflight()
        d = model['decoding']
        body = {'model': model['model_id'], 'messages': [{'role': 'user', 'content': prompt}], 'stream': False,
                # Override every Ollama/Modelfile sampling default with the frozen pilot settings.
                'options': {'temperature': d['temperature'], 'top_p': d['top_p'], 'seed': d['seed'],
                            'num_predict': d['max_tokens'], 'num_ctx': d['num_ctx']}}
        self.requests_sent += 1
        try:
            response = self.client.post(model['endpoint'], json=body)
        except httpx.TimeoutException:
            raise BackendError('transport_timeout_or_network', True) from None
        except httpx.NetworkError:
            raise BackendError('ollama_server_unreachable') from None
        except httpx.HTTPError:
            raise BackendError('transport_error') from None
        if response.status_code != 200:
            raise BackendError(f'http_{response.status_code}', response.status_code in (500, 502, 503, 504))
        try:
            data = response.json()
            if data.get('model') != model['model_id']:
                raise BackendError('served_model_mismatch')
            # 'length' = the model used all max_tokens (a small model can loop). At temperature 0 a retry
            # repeats it, so it is kept and scored as the model's answer (finish_reason records it);
            # without a final marker the evaluator counts it as a parse failure, never as missing data.
            if data.get('done') is not True or data.get('done_reason') not in ('stop', 'length'):
                raise BackendError('incomplete_response')
            text = data['message']['content']
            if not isinstance(text, str) or not text.strip():
                raise BackendError('empty_response', True)
            usage = {target: data[source] for source, target in
                     (('prompt_eval_count', 'prompt_tokens'), ('eval_count', 'completion_tokens'))
                     if type(data.get(source)) is int and data[source] >= 0}
            if len(usage) == 2:
                usage['total_tokens'] = usage['prompt_tokens'] + usage['completion_tokens']
                # Ollama silently drops the start of an over-long prompt; refuse anything that fills the window.
                if usage['total_tokens'] >= d['num_ctx']:
                    raise BackendError('context_window_exceeded')
            else:
                raise BackendError('missing_token_counts')
            return Completion(text, None, usage, data['model'], 'Ollama local', data['done_reason'])
        except (KeyError, TypeError, ValueError):
            raise BackendError('malformed_provider_response') from None
