# Model decision - direct Google AI Studio, free tier

Date checked: 12 November 2026 (PKT). The user selected direct Google AI Studio after OpenRouter's shared free route returned HTTP 429. The requirement remains zero additional project spending.

## Active provider, model and evidence

Provider: **Google AI Studio / Gemini Developer API**, using native REST. Requested model: **`gemma-4-31b-it`**, not a Gemini model. Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent`. Route identity: `google-ai-studio-direct`.

[Google's Gemma API guide](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api) explicitly lists this model and the native endpoint. [Google's pricing table](https://ai.google.dev/gemini-api/docs/pricing#gemma-4) lists Gemma 4 input/output as free of charge, with no paid tier available. Only text generation is used; no tools, grounding, caches, batch jobs, paid models, billing changes or fallback services are requested.

[The official Gemma 4 card](https://ai.google.dev/gemma/docs/core/model_card_4) documents instruction-tuned variants and broad multilingual/reasoning capabilities. This is suitability evidence, not proof of Urdu mathematical accuracy. Urdu fluency, preserved mathematics and response format require actual smoke review. No production research data is available yet.

The model name is a hosted alias, not an immutable weight SHA. Authenticated preflight reads `models/gemma-4-31b-it` metadata and checks exact identity, `generateContent` support and output capacity. Each direct result retains returned `modelVersion`, request ID and model-access metadata, including its version/token limits when supplied. Neither an upstream repository revision nor a dated OpenRouter alias proves the direct API's serving revision. Source/software fingerprints and returned versions improve traceability without guaranteeing bitwise repeatability.

## Free-only guard and account setup

`require_google_free_model` rejects wrong models, endpoints, route names, credential variable names or `free_only: false`. The native request schema is explicitly mapped; OpenRouter price/routing fields are never sent to Google. There is no native per-request dollar-cap parameter, so the safeguards are the fixed Gemma-only allowlist, documented free-only model pricing, no optional paid features and a project without billing attached. Do not claim that an OpenRouter-style price ceiling exists on this API.

Create a key at [Google AI Studio](https://aistudio.google.com/apikey) in a Free tier project. On [Projects](https://aistudio.google.com/projects), identify the project associated with the key and check **Billing Tier**. **Free** with **Set up billing** is the intended state. [Google's billing guide](https://ai.google.dev/gemini-api/docs/billing#verify-billing) states that “Set up billing” means no billing account is attached. Do not click it, attach a card/account, prepay, upgrade or activate a paid trial for this project. If an existing project is billed, use a separate unbilled project instead of modifying unrelated projects.

Save locally in ignored `.env`:

```dotenv
GOOGLE_API_KEY=your_google_ai_studio_key
GOOGLE_AI_STUDIO_FREE_TIER_CONFIRMED=true
```

Set the confirmation true only after checking the key's associated project. The adapter refuses any request until both settings are present. This records **user-confirmed project status**; an API key alone does not let this implementation independently audit Cloud Billing. It does not treat the confirmation as a measured account-billing result. Secrets are passed in `x-goog-api-key`, never in a URL/query or logs. The earlier OpenRouter key is not used by active commands.

## Frozen decoding and runtime policy

| Configuration | Native request |
| --- | --- |
| temperature 0 | `temperature: 0` |
| top_p 1 | `topP: 1` |
| max_tokens 2048 | `maxOutputTokens: 2048` |
| generation seed 42 | `seed: 42` |
| thinking_level minimal | `thinkingConfig: {thinkingLevel: minimal}` |
| one response | `candidateCount: 1` |

[GenerateContent reference](https://ai.google.dev/api/generate-content) documents native fields, finish reasons and usage metadata. [The Gemma-specific guide](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api#thinking) documents `minimal` to disable Gemma hidden thinking. The visible response still includes a requested worked solution. Separate thought parts are excluded from `raw_response`; reported reasoning-token counts are retained. Empty, blocked, malformed or non-STOP outputs are not successful records. No prediction/parser/grading fields are invented.

These parameters succeeded in the four-condition authenticated synthetic smoke and are frozen as of 12 November 2026. Returned model metadata reported version `001`; the response model identifier was `gemma-4-31b-it`. Zero temperature and a seed reduce variation; they do not promise deterministic hosted results. Google recommends sampling for general use; zero temperature is this experiment's control choice. Native preflight checks actual output limits; prompt-context sizing still needs review on the real two-demo prompts.

Timeout: 120 seconds per HTTPX operation. At most three attempts per record. The runner paces starts by at least 3.1 seconds and caps generation attempts at 40 per invocation, including failures/retries. Those are conservative local controls, not a statement of Google's actual quotas. Retry transient transport/408/429/500/502/503/504 errors with bounded waits, honoring Retry-After or structured Google RetryInfo. A wait above 30 seconds defers work. Structured daily-quota exhaustion stops immediately; other exhausted 429 errors halt the remaining matrix. Auth/permission/invalid settings/payment errors are terminal; none trigger an upgrade.

[Current Google rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) are project/model specific and shown in AI Studio; the earlier OpenRouter 50/day limit **does not apply** to this route. Read the active free limits before the real pilot. Eighty calls may require multiple quota windows. Exit 3 means the local request budget left work deferred; resume the same frozen plan after quota permits. No extra keys/projects should be created to evade limits. Direct access avoids OpenRouter's shared routing, but does not guarantee Google capacity.

The API reports token usage, not a measured USD cost. `usage.cost` is omitted rather than fabricated as zero. Free pricing is based on the official table checked on the stated date and the unbilled-project requirement. No payment or paid resource is created.

## Verification and historical route

Native payload/response, metadata checks, key/project gates, sanitization, quotas/pacing, retries and receipt/resume behavior are tested offline with HTTPX MockTransport. Authenticated direct inference is **verified**: all four synthetic conditions succeeded in five generation attempts, with no terminal failures. The user confirmed Free tier and no attached billing account. Resume made zero new requests and left outputs unchanged; the receipt matches the pilot settings. Responses were inspected for visible worked solutions, UTF-8 Urdu and the terminal final marker. This small engineering smoke does not certify Urdu translation quality or measure research accuracy. See `docs/google_live_access_check.json` and the committed live journal. Reproduce using your own key and confirmed free project:

```bash
python -m src.inference.runner run --config configs/live_smoke.yaml --question-limit 1 --resume
```

Direct smoke output: `results/live_smoke/google_direct/smoke.jsonl`; receipt: `results/live_smoke/google_direct/model_verification.json`. The pilot requires that matching receipt. The current receipt is verified and settings are frozen; keep them unchanged for the real pilot. Successful outputs used 922 prompt tokens and 192 completion tokens (1114 total). The API did not report a measured dollar cost; none is invented. No paid fallback or billing change occurred.

OpenRouter's six failed attempts and authenticated zero-spend account check remain in `docs/live_access_check.json`. `configs/openrouter_live_smoke.yaml`, the old adapter and its tests are preserved explicitly for traceability, never as an automatic fallback. Current pilot/live-smoke configs use Google directly. Historical mock journals and manifests are kept without relabeling or overwriting them.
