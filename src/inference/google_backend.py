"""Direct AI Studio REST adapter for the selected free Gemma model.

No OpenRouter routing, SDK defaults, tools, fallback models or billing changes.
"""
from copy import deepcopy
import os
import time

import httpx

from src.inference.backends import BackendError, Completion, retry_delay
from src.inference.free_policy import (GOOGLE_FREE_TIER_ENV, GOOGLE_MODEL_URL,
                                       require_google_free_model, verify_google_model)


def google_http_error(response):
    """Keep provider bodies out of logs; use only structured retry/quota information."""
    status = response.status_code
    wait = retry_delay(response.headers.get('retry-after'))
    daily_quota = False
    try:
        error = response.json().get('error', {})
        for detail in error.get('details', []):
            kind = detail.get('@type', '')
            if kind.endswith('google.rpc.RetryInfo') and wait is None:
                delay = detail.get('retryDelay', '')
                if isinstance(delay, str) and delay.endswith('s'):
                    wait = retry_delay(delay[:-1])
            if kind.endswith('google.rpc.QuotaFailure'):
                for violation in detail.get('violations', []):
                    quota = str(violation.get('quotaId', '')).lower()
                    quota += str(violation.get('quotaMetric', '')).lower()
                    if 'perday' in quota or 'per_day' in quota:
                        daily_quota = True
    except (ValueError, TypeError, AttributeError):
        pass
    if status == 429 and daily_quota:
        return BackendError('google_daily_quota_exhausted')
    return BackendError(f'http_{status}', status in (408, 429, 500, 502, 503, 504), wait)


class GoogleAIStudioBackend:
    def __init__(self, model, client=None, sleep=time.sleep, monotonic=time.monotonic):
        require_google_free_model(model)
        self.model = deepcopy(model)
        self.key = os.environ.get('GOOGLE_API_KEY', '')
        if not self.key or self.key == 'replace_with_your_google_ai_studio_key':
            raise ValueError('Set GOOGLE_API_KEY in ignored .env using a Free tier Google AI Studio project; no billing upgrade')
        if os.environ.get(GOOGLE_FREE_TIER_ENV, '').lower() != 'true':
            raise ValueError('Confirm the Google project is Free tier with billing disabled, then set GOOGLE_AI_STUDIO_FREE_TIER_CONFIRMED=true in ignored .env')
        # This is the user's explicit project-tier confirmation, not an API billing audit.
        self.free_tier_confirmed = True
        self.client = client or httpx.Client(timeout=model['timeout_seconds'], follow_redirects=False)
        self.sleep, self.monotonic = sleep, monotonic
        self.requests_sent, self.last_request = 0, None
        self.catalog_evidence = None

    @property
    def requests_remaining(self):
        return self.model['max_requests_per_invocation'] - self.requests_sent

    def generate(self, prompt, model):
        if model != self.model:
            raise BackendError('free_policy_model_changed')
        if not self.requests_remaining:
            raise BackendError('free_request_budget_exhausted')
        headers = {'x-goog-api-key': self.key}
        try:
            if self.catalog_evidence is None:
                response = self.client.get(GOOGLE_MODEL_URL, headers=headers)
                if response.status_code != 200:
                    raise google_http_error(response)
                try:
                    self.catalog_evidence = verify_google_model(response.json(), model)
                except ValueError:
                    raise BackendError('google_model_preflight_failed') from None
            if self.last_request is not None:
                delay = model['min_request_interval_seconds'] - (self.monotonic() - self.last_request)
                if delay > 0:
                    self.sleep(delay)
            decoding = model['decoding']
            body = {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                    'generationConfig': {'temperature': decoding['temperature'], 'topP': decoding['top_p'],
                                         'maxOutputTokens': decoding['max_tokens'], 'seed': decoding['seed'],
                                         'candidateCount': 1,
                                         'thinkingConfig': {'thinkingLevel': decoding['thinking_level']}}}
            self.last_request = self.monotonic()
            self.requests_sent += 1  # Count every submitted generation attempt, including failures.
            response = self.client.post(model['endpoint'], json=body, headers=headers)
        except (httpx.TimeoutException, httpx.NetworkError):
            raise BackendError('transport_timeout_or_network', True) from None
        except httpx.HTTPError:
            raise BackendError('transport_error') from None
        if response.status_code != 200:
            raise google_http_error(response)
        try:
            data = response.json()
            if data.get('promptFeedback', {}).get('blockReason'):
                raise BackendError('google_prompt_blocked')
            candidate = data['candidates'][0]
            if candidate.get('finishReason') != 'STOP':
                raise BackendError('incomplete_response')
            parts = candidate['content']['parts']
            # Preserve all visible text, without leaking a separate hidden thought part into raw_response.
            text = ''.join(part['text'] for part in parts
                           if isinstance(part, dict) and isinstance(part.get('text'), str)
                           and not part.get('thought', False))
            if not text.strip():
                raise BackendError('empty_response', True)
            source_usage = data.get('usageMetadata', {})
            mapping = {'promptTokenCount': 'prompt_tokens', 'candidatesTokenCount': 'completion_tokens',
                       'totalTokenCount': 'total_tokens', 'thoughtsTokenCount': 'reasoning_tokens'}
            usage = {target: source_usage[source] for source, target in mapping.items()
                     if type(source_usage.get(source)) is int and source_usage[source] >= 0}
            # The API does not return a measured USD cost; never fabricate usage.cost=0.
            return Completion(text.replace(self.key, '[REDACTED]'),
                              data.get('responseId') or response.headers.get('x-request-id'), usage,
                              data.get('modelVersion'), 'Google AI Studio direct', candidate['finishReason'])
        except (KeyError, IndexError, TypeError, ValueError):
            raise BackendError('malformed_provider_response') from None
