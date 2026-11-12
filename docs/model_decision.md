# Model decision - 12 November 2026 (PKT)

## Decision and evidence

Proposed API gateway: OpenRouter. Exact requested model ID: `qwen/qwen3-235b-a22b-2507`, corresponding to Qwen's `Qwen3-235B-A22B-Instruct-2507` release. Pin routing to `deepinfra/fp8` with `provider.only`, `allow_fallbacks: false` and `require_parameters: true`. This prevents silent routing to an engine that ignores experimental settings. Use one route and one model throughout the pilot.

[Qwen's model card](https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507) describes a multilingual instruction-tuned release with 235B total/22B active parameters and non-thinking generation. It is suitable for few-shot mathematical reasoning without downloading weights. [Qwen's family announcement](https://qwenlm.github.io/blog/qwen3/) explicitly lists Urdu among 119 supported languages/dialects. This is family-level suitability evidence, not evidence of accuracy on this project's Urdu data; human smoke review remains necessary.

[OpenRouter's model page](https://openrouter.ai/qwen/qwen3-235b-a22b-2507) and its [public endpoint catalog](https://openrouter.ai/api/v1/models/qwen/qwen3-235b-a22b-2507/endpoints) were checked on 12 November 2026. The catalog lists DeepInfra FP8 with 262,144 context tokens, max completion 16,384, and support for temperature, top-p, max tokens and seed. A small selected-field catalog snapshot is committed alongside this document. Availability can change independently of the model page.

The release suffix is dated July 2025; the API offers no immutable weight SHA or serving-engine revision guarantee. A public model-card repository revision can identify source weights, but cannot prove what the hosted endpoint serves. Record requested and returned model/provider identifiers per response and preserve the catalog snapshot, route, configuration and date. An API alias, quantization implementation, engine or server can change. Temperature zero and a fixed seed reduce variation but cannot guarantee bitwise reproducibility.

## Request and decoding contract

Use HTTPS `POST https://openrouter.ai/api/v1/chat/completions`, one user message containing the complete prompt, nonstreaming response. Authentication variable: **OPENROUTER_API_KEY**. Configure in an ignored `.env` or exported environment. No resource provisioning or weights download is needed. The key must have available credit/permission for this route.

Fixed proposed request settings:

| Setting | Value |
| --- | --- |
| temperature | 0 |
| top_p | 1 |
| max_tokens | 2048 |
| generation seed | 42 |
| selection seed | 42, independently recorded |
| stream | false |
| route | deepinfra/fp8 only |
| parameter support enforcement | true |

[OpenRouter parameters](https://openrouter.ai/docs/api/reference/parameters) and [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection) document these controls. We send only the supported subset. No `enable_thinking`, reasoning budget, reasoning effort or reasoning-token parameter is sent: this Instruct release has no thinking mode. The [Qwen quickstart](https://github.com/QwenLM/Qwen3/blob/main/docs/source/getting_started/quickstart.md) states that `enable_thinking=False` is not supported for this release. Qwen recommends sampling for general use; zero temperature is an experimental-control choice here, to be reviewed in the smoke test.

The 2048-token output cap bounds cost; Urdu text can use more tokens than English. The 262,144-token context limit applies to prompt plus completion. Two short demonstrations should fit easily; the runner does not implement a provider tokenizer or claim exact preflight token counts. Inspect token usage and increase the cap only after a new smoke test and before freezing the experiment. Any non-`stop` finish reason is a terminal `incomplete_response` failure rather than a complete answer. Empty output is retried within the same bounded policy, then recorded as failure.

## Timeouts, retries and costs

HTTP timeout: 120 seconds per HTTPX operation, not an absolute total wall-clock deadline. At most three attempts per record. Retry transport timeout/network errors and HTTP 408/429/500/502/503/504, with 1/2-second fallback waits. Respect numeric or HTTP-date `Retry-After`; a wait above 30 seconds becomes `retry_after_exceeds_wait_budget` for a later resume, with no early retry. HTTP 402 is retried only when accompanied by a valid retry header. Invalid parameters/credentials/permissions are not repeatedly retried. Provider errors inside HTTP 200 bodies are also recognized. See [official error documentation](https://openrouter.ai/docs/api/reference/errors-and-debugging).

Catalog price checked **12 November 2026** for this specific DeepInfra route: **$0.09 per million input tokens; $0.55 per million output tokens**. These are dated quoted prices, not a guarantee or an account billing verification. For illustration, 80 calls at 2,000 input tokens and 2,048 output tokens would cost about $0.105 before retries/other fees: (160,000 × 0.09 + 163,840 × 0.55) / 1,000,000. Actual tokenization, response length, retries, billing and rates determine the cost. No paid resources were created. Sequential execution and rate limits can dominate runtime; there is no guaranteed completion-time estimate.

## Verification status and freeze procedure

Public documentation and unauthenticated endpoint metadata: checked. Adapter payload, normal response, sanitized failures and retry behavior: tested offline with HTTPX MockTransport. **Authenticated live inference: not verified.** No relevant credential variable was present and no local model runtime was available in the workspace. No real development data was present.

Provide `OPENROUTER_API_KEY` and access/credits on OpenRouter, then run:

```bash
python -m src.inference.runner run --config configs/live_smoke.yaml --question-limit 1 --resume
```

Four successful synthetic condition records create a secret-free `results/live_smoke/model_verification.json` receipt with model settings hash, successful IDs and journal hash. Inspect actual Urdu and English outputs. The real runner requires a matching receipt, so configuration remains explicitly proposed/unverified until live success. Do not edit frozen model settings mid-pilot. Commit the reviewed settings and, after secret/provenance checks, the small live verification receipt/results if useful for reproducibility (they are ignored by default). Revalidate availability before spending on the real pilot.
