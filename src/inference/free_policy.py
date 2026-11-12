"""The user's zero-spend constraint. Paid routes are never an integration option."""
from decimal import Decimal, InvalidOperation

FREE_MODEL_ID = 'google/gemma-4-31b-it:free'
FREE_ROUTE = 'google-ai-studio'
ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
CATALOG_URL = 'https://openrouter.ai/api/v1/models/' + FREE_MODEL_ID + '/endpoints'
ZERO_PRICE_CAP = {'prompt': 0, 'completion': 0, 'request': 0}


def require_free_model(model):
    if (model.get('free_only') is not True or model.get('model_id') != FREE_MODEL_ID
            or model.get('route') != FREE_ROUTE or model.get('endpoint') != ENDPOINT
            or model.get('credential_env') != 'OPENROUTER_API_KEY'):
        raise ValueError('Zero-cost policy: only the configured Gemma :free model and free provider are allowed; paid routes are disabled')


def verify_catalog(data, model):
    """Fail closed on missing/nonzero prices, missing route or unsupported parameters."""
    try:
        catalog = data['data']
        if catalog['id'] != FREE_MODEL_ID:
            raise ValueError
        endpoint = next(e for e in catalog['endpoints'] if e['tag'] == FREE_ROUTE)
        pricing = endpoint['pricing']
        if not {'prompt', 'completion'} <= pricing.keys():
            raise ValueError
        for key, value in pricing.items():
            if key == 'discount':
                continue
            amount = Decimal(str(value))
            if not amount.is_finite() or amount != 0:
                raise ValueError
        if not set(model['decoding']) <= set(endpoint['supported_parameters']):
            raise ValueError
        if model['decoding']['max_tokens'] > endpoint['max_completion_tokens']:
            raise ValueError
        return {k: endpoint[k] for k in ('tag', 'pricing', 'supported_parameters', 'context_length', 'max_completion_tokens')}
    except (KeyError, TypeError, ValueError, StopIteration, InvalidOperation):
        raise ValueError('Free route preflight failed: route unavailable, nonzero/unknown pricing, or unsupported settings; no inference sent') from None


GOOGLE_MODEL_ID = 'gemma-4-31b-it'
GOOGLE_ROUTE = 'google-ai-studio-direct'
GOOGLE_MODEL_URL = 'https://generativelanguage.googleapis.com/v1beta/models/' + GOOGLE_MODEL_ID
GOOGLE_ENDPOINT = GOOGLE_MODEL_URL + ':generateContent'
GOOGLE_FREE_TIER_ENV = 'GOOGLE_AI_STUDIO_FREE_TIER_CONFIRMED'


def require_google_free_model(model):
    if (model.get('free_only') is not True or model.get('model_id') != GOOGLE_MODEL_ID
            or model.get('route') != GOOGLE_ROUTE or model.get('endpoint') != GOOGLE_ENDPOINT
            or model.get('credential_env') != 'GOOGLE_API_KEY'):
        raise ValueError('Zero-cost policy: direct Google access permits the documented free Gemma model only; no Gemini or paid fallback')


def verify_google_model(data, model):
    try:
        if data['name'] != 'models/' + GOOGLE_MODEL_ID or 'generateContent' not in data['supportedGenerationMethods']:
            raise ValueError
        if (type(data['outputTokenLimit']) is not int
                or model['decoding']['max_tokens'] > data['outputTokenLimit']):
            raise ValueError
        return {k: data[k] for k in ('name', 'version', 'inputTokenLimit', 'outputTokenLimit', 'supportedGenerationMethods')}
    except (KeyError, TypeError, ValueError):
        raise ValueError('Direct Google model preflight failed; model identity, generation support or output limit is incompatible') from None
