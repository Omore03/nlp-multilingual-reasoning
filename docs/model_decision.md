# Model setup

Model access verified 12 November; official model/pricing pages checked again 25 November 2026 (PKT).

## Selected model

| Item | Value |
| --- | --- |
| Provider | Direct Google AI Studio / Gemini Developer API |
| Model | `gemma-4-31b-it` |
| API | Native REST `generateContent` |
| Endpoint | `https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent` |
| Observed model metadata version | `001` |
| Observed input / output limits | 262144 / 32768 tokens |
| Verification | Four-condition synthetic access smoke; 80 reviewed-data pilot responses completed 25 November |

The [Gemma API guide](https://gemma.ai/deployment/gemini-api/) documents the model and endpoint. The [model card](https://ai.google.dev/gemma/docs/core/model_card_4) describes multilingual reasoning capabilities. The real reviewed-data collection is recorded in [verification](verification.md).

The hosted model name can change behind the alias. We record returned versions and request metadata, but cannot guarantee identical hosted responses across runs.

## Keep it free

Google's [pricing table](https://aistudio.google.com/docs/pricing), checked on the date above, listed Gemma 4 input/output as free with no paid tier. The adapter permits only the configured Gemma model and endpoint. It uses no paid fallback or optional paid features.

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

The adapter maps these to [native generation fields](https://ai.google.dev/api/generate-content). The [Gemma thinking guide](https://gemma.ai/deployment/gemini-api/#thinking) explains the thinking setting. Separate thought parts are excluded from the saved response; the requested worked solution remains visible. Empty, blocked, malformed or non-STOP completions fail validation.

These settings passed the live smoke and are frozen in `configs/pilot.yaml` and its matching receipt. A seed and zero temperature reduce variation without guaranteeing determinism. Check actual prompt lengths before the real pilot.

## Quotas and evidence

[Free quotas](https://ai.google.dev/gemini-api/docs/rate-limits) vary by project and model. The local 40-attempt budget is a runner limit, not Google's published quota. The 80-record pilot may span multiple quota windows. Wait and resume rather than upgrading or evading quotas.

Transient errors have bounded retries. Daily quota, auth and invalid settings stop the run. Repeated HTTP 503 capacity errors fail a record after bounded retries; later records may continue. Exit 3 indicates local-budget deferral. See the [run guide](running.md) for recovery and other exit codes.

The recorded smoke produced four successes in five generation attempts, using 1114 tokens across successful responses. The API supplied no measured dollar cost, so no cost value was invented. See [verification](verification.md), the [sanitized access record](google_live_access_check.json) and the [model receipt](../results/live_smoke/google_direct/model_verification.json).

The earlier OpenRouter route returned upstream capacity errors. Its adapter, config and evidence remain historical; active commands use Google directly with no automatic fallback.

## Small-model arm: local Gemma 3 1B (25 Nov 2026)

The Gemma 4 31B pilot scored 80/80, a ceiling that hides any strategy or language effect. A second arm reruns the identical plan (same data, frozen selections, all 80 prompts byte-identical, same decoding) with a smaller model from the same family. Only the model changes. Google's API no longer serves Gemma 3, so it runs locally through Ollama on Rayyan's laptop. This is a local branch for team review and is not merged.

| Setting | Value |
| --- | --- |
| Model | `gemma3:1b` (Gemma 3 1B instruction-tuned), Q4_K_M, 999.89M parameters |
| Pinned digest | `97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c`, checked against `/api/tags` before the first call |
| Runtime | Ollama 0.40.18 (Homebrew), Apple M5 GPU (Metal), `http://127.0.0.1:11434/api/chat` |
| Temperature / top-p / seed | 0 / 1 / 42, sent on every call to override the Modelfile defaults (temperature 1, top-k 64, top-p 0.95) |
| Maximum output / context | 2048 tokens / 4096 tokens (`num_ctx` fixed, not the VRAM-based default) |
| Attempts, quotas, pacing | 3 attempts per record; no request budget or spacing (local, zero cost) |
| Configs | `configs/ollama_gemma3_1b_smoke.yaml` (receipt), `configs/pilot_ollama_gemma3_1b.yaml` (real run) |
| Output | `results/gemma3_1b/`; the 31B arm in `results/pilot_raw.jsonl` is untouched |

A response that fills the 2048-token limit (`finish_reason: length`, typically a small model repeating itself) is kept and scored as returned, because a temperature-0 retry repeats it. Without a final marker it counts as a parse failure. Calls that fill the 4096-token context, return another model, or fail the digest check are rejected. The first attempt, which treated length cut-offs as call failures, was stopped after 6 records and kept in `results/gemma3_1b/aborted_run1_length_as_failure/`.

## Small-model arm: local Gemma 3 4B, and zero-shot baselines (25 Nov 2026)

The 1B arm left Urdu at the floor (U-U-U 0/20), so the decision rule called for the 4B backup. It uses the same runner, decoding and plan; only the model block changes.

| Setting | Value |
| --- | --- |
| Model | `gemma3:4b` (Gemma 3 4B instruction-tuned), Q4_K_M, 3.9B parameters, 3.35 GB (includes the unused vision projector) |
| Pinned digest | `68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7` |
| Configs | `configs/ollama_gemma3_4b_smoke.yaml`, `configs/pilot_ollama_gemma3_4b.yaml`, `configs/zeroshot_ollama_gemma3_4b.yaml` |
| Output | `results/gemma3_4b/`, `results/gemma3_4b_zeroshot/` |

**Zero-shot baseline** (`shot_count: 0`, `strategies: [none]`, `selector: null`, template `bilingual-math-0shot-v1`): the same instruction minus the "follow the solved demonstrations" sentence, then the target question. With no demonstrations the demonstration language has no effect, so U-E-E would duplicate U-U-E; only U-U-U, U-U-E and E-E-E are run (30 calls per model), as `docs/evaluation_plan.md` anticipates. Configs: `configs/zeroshot_ollama_gemma3_{1b,4b}.yaml`. The two-shot prompts remain byte-identical to the 31B run.

**Parser (changed 25 Nov, pending Saad's approval).** Some correct 4B answers were scored as parse failures: `FINAL_ANSWER 70` (no colon), or a generic "final answer:" followed by a restated question, read as a second answer. Parser version 2 lets the last `FINAL_ANSWER` followed by a number decide (colon optional) and keeps the earlier rule as a fallback. All runs were re-scored from their raw files: 15 answers gained, none lost, 31B unchanged. Details, evidence and how to revert: [parser change](parser_change_2026-11-25.md).

## Seed-variance check for random selection, Gemma 3 4B (25 Nov 2026)

`configs/seedcheck_ollama_gemma3_4b_seed43.yaml` and `..._seed44.yaml` rerun random selection only, with base selection seeds 43 and 44 instead of 42 (all four conditions, 40 calls each). The generation seed stays 42 and everything else is unchanged, so only the random demonstration pairs differ (all 10 pairs change for each seed). These runs use the live random selector `src.selection.select:select_examples`, which reproduces the frozen seed-42 random pairs 10/10; no encoder is involved. The runner now accepts random-only real runs for this purpose. Output: `results/gemma3_4b_seed43/`, `results/gemma3_4b_seed44/`; the seed table is in `docs/model_comparison.md`.
