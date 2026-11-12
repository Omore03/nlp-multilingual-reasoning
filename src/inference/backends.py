"""One provider-specific real adapter and a deterministic engineering mock."""
import hashlib
import os
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx


class BackendError(Exception):
    def __init__(self, code, transient=False, retry_after=None):
        super().__init__(code)  # Never include response bodies, URLs, or headers.
        self.code, self.transient, self.retry_after = code, transient, retry_after


@dataclass
class Completion:
    text: str
    request_id: str | None = None
    usage: dict | None = None
    served_model: str | None = None
    served_provider: str | None = None
    finish_reason: str | None = None


class MockBackend:
    def generate(self, prompt, model):
        digest = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
        return Completion(f'MOCK ENGINEERING RESPONSE {digest[:16]}. No mathematical solution was computed.\n'
                          'FINAL_ANSWER: 0', 'mock-' + digest[:20], {}, model['model_id'], 'mock', 'stop')


def retry_delay(value):
    if value is None:
        return None
    try:
        number = float(value)
        return max(0.0, number) if math.isfinite(number) else None
    except ValueError:
        try:
            return max(0.0, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


class OpenRouterBackend:
    def __init__(self, model, client=None):
        key = os.environ.get(model['credential_env'], '')
        if not key or key == 'replace_with_your_openrouter_key':
            raise ValueError('Set OPENROUTER_API_KEY in the environment or ignored .env before live inference')
        self.key = key
        self.client = client or httpx.Client(timeout=model['timeout_seconds'], follow_redirects=False)

    def generate(self, prompt, model):
        body = {'model': model['model_id'], 'messages': [{'role': 'user', 'content': prompt}],
                **model['decoding'], 'stream': False,
                'provider': {'only': [model['route']], 'allow_fallbacks': False, 'require_parameters': True}}
        try:
            response = self.client.post(model['endpoint'], json=body,
                                        headers={'Authorization': 'Bearer ' + self.key})
        except (httpx.TimeoutException, httpx.NetworkError):
            raise BackendError('transport_timeout_or_network', True) from None
        except httpx.HTTPError:
            raise BackendError('transport_error') from None
        if response.status_code != 200:
            status = response.status_code
            wait = retry_delay(response.headers.get('retry-after'))
            transient = status in (408, 429, 500, 502, 503, 504) or (status == 402 and wait is not None)
            raise BackendError(f'http_{status}', transient, wait)
        try:
            data = response.json()
            if 'error' in data:
                code = int(data['error'].get('code', 0))
                wait = retry_delay(response.headers.get('retry-after'))
                raise BackendError(f'provider_error_{code}', code in (408, 429, 500, 502, 503, 504), wait)
            choice = data['choices'][0]
            text = choice['message']['content']
            if not isinstance(text, str) or not text.strip():
                raise BackendError('empty_response', True)
            if choice.get('finish_reason') != 'stop':
                raise BackendError('incomplete_response')
            # Only retain documented safe numeric usage metadata.
            usage = {k: v for k, v in data.get('usage', {}).items()
                     if k in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cost')
                     and type(v) in (int, float)}
            return Completion(text.replace(self.key, '[REDACTED]'), data.get('id'), usage,
                              data.get('model'), data.get('provider'), choice.get('finish_reason'))
        except (KeyError, IndexError, TypeError, ValueError):
            raise BackendError('malformed_provider_response') from None


def call_with_retries(backend, prompt, model, sleep=time.sleep):
    for attempt in range(1, model['max_attempts'] + 1):
        try:
            result = backend.generate(prompt, model)
            if not isinstance(result.text, str) or not result.text.strip():
                raise BackendError('empty_response', True)
            return result, attempt
        except BackendError as exc:
            if not exc.transient or attempt == model['max_attempts']:
                exc.attempts = attempt
                raise
            delay = exc.retry_after if exc.retry_after is not None else min(2 ** (attempt - 1), 30)
            # A long provider wait is preserved as a terminal failure for a later resume.
            if delay > model['max_retry_wait_seconds']:
                error = BackendError('retry_after_exceeds_wait_budget')
                error.attempts = attempt
                raise error from None
            sleep(delay)
