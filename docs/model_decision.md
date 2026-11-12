# Free-only model decision - 12 November 2026 (PKT)

## Hard budget and selected model

The user requires **zero additional project spending**. No credit purchases, paid API requests, paid fallbacks, trials requiring payment, rented GPUs or subscriptions are part of this project. The earlier paid Qwen configuration is superseded and rejected by current code. Local tests and mock runs use existing hardware. Hosted Actions automation has been removed; verification is local so it cannot consume billable runner time.

Proposed live model: **`google/gemma-4-31b-it:free`**, via OpenRouter, restricted to **`google-ai-studio`**. [The official endpoint catalog](https://openrouter.ai/api/v1/models/google/gemma-4-31b-it:free/endpoints), checked 12 November 2026, lists zero input/output pricing, a 262,144-token context and 32,768 max completion tokens. Its endpoint name references `google/gemma-4-31b-it-20260402:free`; this is descriptive provider metadata, not an immutable serving revision. The committed `docs/model_catalog_snapshot.json` records selected public metadata and the upstream repository revision, which does not prove the hosted weights match it.

[Google's model card](https://ai.google.dev/gemma/docs/core/model_card_4) describes Gemma 4's instruction-tuned variants, mathematical/reasoning use and broad multilingual coverage (pretraining in over 140 languages). This supports trying the model for this pilot, but the cited material does not establish Urdu-specific mathematical accuracy or translation quality. Those remain explicitly unverified until actual Urdu/English smoke review. No final model-quality claim follows from a free endpoint being listed.

Use a single named model, not `openrouter/free`, which may choose different models per request. Preserve model/provider and settings across conditions and quota days. Availability, weights, chat-template implementation and engine revisions can change; the requested identifier is not a reproducible weight SHA. Record returned model/provider identifiers and timestamps. No weights are downloaded.

## Enforced zero-price request policy

`src/inference/free_policy.py` centralizes the model, provider and endpoint allowlist. Both config validation and direct adapter construction reject paid/wrong models or `free_only: false`. Before the first inference, the adapter fetches public endpoint metadata and refuses missing/nonzero pricing, a missing provider, insufficient output limits or unsupported requested parameters. A changed catalog therefore stops inference instead of selecting another model.

Every text-only request sends one user message with the full bilingual prompt to `https://openrouter.ai/api/v1/chat/completions`, with no plugins, tools, paid transformations or fallback models. Provider preferences are:

```json
{"only":["google-ai-studio"],"allow_fallbacks":false,"require_parameters":true,"max_price":{"prompt":0,"completion":0,"request":0}}
```

[Official provider routing](https://openrouter.ai/docs/guides/routing/provider-selection) documents price ceilings and support enforcement. Combined with the explicit `:free` ID and live zero-price preflight, these are the request-level spending safeguards; no paid route is an option. If the provider unexpectedly reports positive cost, the runner records a policy failure and halts rather than continuing. A missing cost field is not fabricated as a measured zero; the request remains constrained to a free route.

## Decoding and access

| Setting | Proposed value |
| --- | --- |
| temperature | 0 |
| top_p | 1 |
| max_tokens | 2048 |
| generation seed | 42 |
| selection seed | 42, independently recorded |
| reasoning | `{"enabled": false}` |
| stream | false |
| minimum interval | 3.1 seconds between request starts |
| max API attempts per invocation | 40, including failed/transient attempts |

The current endpoint advertises support for these decoding keys. [OpenRouter reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens) document disabling reasoning; [Google's thinking guidance](https://ai.google.dev/gemma/docs/capabilities/thinking) distinguishes hidden thinking from final response generation and notes provider/template handling. The prompt still requests a complete visible worked solution. Inspect actual outputs for hidden thought leakage, truncation, Urdu fluency and final-marker adherence. Temperature zero is an experimental-control choice; it does not guarantee bitwise reproducibility across engines or days. Google recommends sampling for general use; that differs from this controlled pilot choice.

Authentication variable: **OPENROUTER_API_KEY**, in an ignored `.env` or exported environment. Create a free account/key; no card, funded balance, credit purchase or upgrade is required for a `:free` variant. If an account/region is denied access, stop and document it; do not fund the account or use a paid model as a workaround. [OpenRouter's free-model documentation](https://openrouter.ai/collections/free-models/) explicitly states that free variants require no purchase and currently allow 20 requests/minute and 50/day on an unfunded account; failed attempts count and usage is shared across free models.

## Quotas, failures and resumption

The 80-record real pilot plus four-condition live verification needs **at least two daily quota windows**, assuming enough free capacity and no excessive failures/other account usage. Leave the API key unfunded and wait for quota resets. Do not create additional accounts/keys to evade limits. Capacity can make completion take longer. No promised same-day deadline or provider SLA is assumed.

The adapter paces all attempts, including retries. At most 40 API attempts are permitted per invocation; when exhausted, the runner saves completed records, reports deferred work and exits 3. Resume the same output after quota resets. A recognized exhausted daily quota stops immediately without retries; other exhausted 429/retry-wait errors also halt the remaining matrix. The per-invocation budget is a conservative local cap, not a replacement for the provider's shared daily counter. Repeated invocations do not reset the account's quota.

HTTP timeout remains 120 seconds per operation. At most three attempts per record, within the invocation budget; fallback waits 1/2 seconds, provider Retry-After respected. Waits above 30 seconds are deferred with a failure record. HTTP 400/401/402/403/404/422 are terminal; **402 never triggers a payment or a retry-to-purchase path**. Blank/malformed/incomplete completions are not successful records. An interruption after a remote call but before durable append can consume an extra free request on resume.

## Actual verification status

Public catalog/documentation: checked. Payload, zero-price gates, quota/pacing, retries and resume: tested offline. **Authenticated inference, account access, provider-reported usage and Urdu quality remain unverified.** The existing local `.env` has only a placeholder. No paid or live inference was performed.

```bash
python -m src.inference.runner run --config configs/live_smoke.yaml --question-limit 1 --resume
```

After four successful free synthetic conditions, inspect outputs and retain the automatic `results/live_smoke/model_verification.json` receipt. It links model settings and successful output IDs by hashes. Only then use the matching model for real data. Current live output is `results/live_smoke/gemma_free_smoke.jsonl`, so the earlier blocked preflight manifest is preserved separately. Changing model/settings/source requires a new run identity; never relabel mock data as live verification.
