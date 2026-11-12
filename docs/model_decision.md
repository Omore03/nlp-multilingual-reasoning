# Model setup

Recorded verification date: 12 November 2026 (PKT).

## Selected model

| Item | Value |
| --- | --- |
| Provider | Direct Google AI Studio / Gemini Developer API |
| Model | `gemma-4-31b-it` |
| API | Native REST `generateContent` |
| Endpoint | `https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent` |
| Observed model metadata version | `001` |
| Observed input / output limits | 262144 / 32768 tokens |
| Verification | Four successful live conditions on synthetic questions |

The [Gemma API guide](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api) documents the model and endpoint. The [model card](https://ai.google.dev/gemma/docs/core/model_card_4) describes multilingual reasoning capabilities. Actual Urdu mathematical accuracy still needs evaluation on the reviewed data.

The hosted model name can change behind the alias. We record returned versions and request metadata, but cannot guarantee identical hosted responses across runs.

## Keep it free

Google's [pricing table](https://ai.google.dev/gemini-api/docs/pricing#gemma-4), checked on the date above, listed Gemma 4 input/output as free with no paid tier. The adapter permits only the configured Gemma model and endpoint. It uses no paid fallback or optional paid features.

Create a key in [AI Studio](https://aistudio.google.com/apikey). Check its project in [Projects](https://aistudio.google.com/projects): it must show **Free** and **Set up billing**. Google's [billing guide](https://ai.google.dev/gemini-api/docs/billing#verify-billing) explains that this means no billing account is attached. Leave billing disabled.

Save these settings in ignored `.env`:

```dotenv
GOOGLE_API_KEY=your_key_here
GOOGLE_AI_STUDIO_FREE_TIER_CONFIRMED=true
```

The confirmation records the user's project check; it is not an independent billing audit. Calls are blocked without both settings. The key is sent in a header and excluded from logs and manifests. No credits, card, paid compute or subscription are required.

## Fixed inference settings

| Setting | Value |
| --- | --- |
| Temperature / top-p | 0 / 1 |
| Generation seed | 42 |
| Maximum output | 2048 tokens |
| Thinking level | `minimal` |
| Responses per request | 1 |
| HTTPX operation timeout | 120 seconds |
| Maximum attempts per record | 3 |
| Maximum retry wait | 30 seconds |
| Request spacing | At least 3.1 seconds |
| Generation budget per invocation | 40 attempts, including retries |

The adapter maps these to [native generation fields](https://ai.google.dev/api/generate-content). The [Gemma thinking guide](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api#thinking) explains the thinking setting. Separate thought parts are excluded from the saved response; the requested worked solution remains visible. Empty, blocked, malformed or non-STOP completions fail validation.

These settings passed the live smoke and are frozen in `configs/pilot.yaml` and its matching receipt. A seed and zero temperature reduce variation without guaranteeing determinism. Check actual prompt lengths before the real pilot.

## Quotas and evidence

[Free quotas](https://ai.google.dev/gemini-api/docs/rate-limits) vary by project and model. The local 40-attempt budget is a runner limit, not Google's published quota. The 80-record pilot may span multiple quota windows. Wait and resume rather than upgrading or evading quotas.

Transient errors have bounded retries. Daily quota, auth, invalid settings and exhausted capacity stop the run. Exit 3 indicates local-budget deferral. See the [run guide](running.md) for recovery and other exit codes.

The recorded smoke produced four successes in five generation attempts, using 1114 tokens across successful responses. The API supplied no measured dollar cost, so no cost value was invented. See [verification](verification.md), the [sanitized access record](google_live_access_check.json) and the [model receipt](../results/live_smoke/google_direct/model_verification.json).

The earlier OpenRouter route returned upstream capacity errors. Its adapter, config and evidence remain historical; active commands use Google directly with no automatic fallback.
