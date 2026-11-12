# Executed engineering verification - free-only revision

Date: 12 November 2026 (PKT). The user requires zero additional project spending. No model API call, credit purchase, paid service, compute rental or subscription was made.

## Current executed checks

| Check | Actual outcome |
| --- | --- |
| `python -m pytest -q` | **66 passed**, fully offline |
| Mock preview, one question/two labels | 8 UTF-8 prompt records |
| Four-condition mock smoke | 4 successful mock records |
| Full mock matrix | 80 unique successful records, zero failures |
| Resume | 0 new successes; prior matrix byte-for-byte unchanged |
| Free live prompt preview | Succeeded without inference |
| Free live inference attempt | Blocked before any model call: `OPENROUTER_API_KEY` is still a placeholder |
| Public free endpoint catalog and Google model documentation | Checked; catalog reports zero pricing and required parameter support |
| Paid-ID/config/direct-adapter rejection | Passed offline |
| Missing/nonzero catalog pricing and wrong/unsupported route rejection | Passed; no inference POST sent |
| Zero request price ceilings, fixed provider and fallback disabled | Verified in captured HTTPX mock payloads |
| Unexpected provider-reported cost | Stops the invocation with a policy failure |
| API-attempt budget, 3.1-second pacing and partial resume | Passed using an injected clock and simulated responses |
| Recognized exhausted daily quota | Stops after one failed attempt without retries or remaining-matrix calls |

The suite also retains prompt language/order/completeness, target-gold exclusion, selector boundary, ID/schema separation, UTF-8, required metadata, retry/failure, locking, incompatible-run and explicit tail-recovery tests. `pytest.ini` restricts discovery to `tests/` so local ignored reproduction checkouts do not cause duplicate test-module discovery.

Current reviewable artifacts: `results/mock/free_preview.jsonl`, `results/mock/free_smoke.jsonl`, `results/mock/free_matrix.jsonl` and adjacent smoke/matrix manifests. All are synthetic/mock engineering artifacts. No mathematical accuracy, Urdu model quality or selector research result is claimed.

Current matrix SHA-256, unchanged after no-op resume:

```text
370355b7c209525b653afcbe2a92fe57e7930abcbd8e68566aab8a0def04029f
```

Earlier `preview.jsonl`, `smoke.jsonl`, `matrix.jsonl` and their manifests are preserved historical mock evidence from the initial implementation. Their source/settings fingerprints intentionally differ. The initial revision had 51 passing offline tests and passed a clean local clone with standard venv/pip setup, prompt preview, mock smoke, full matrix and resume. That historical clean-clone check does not imply the new free live route was tested with credentials.

HTTPX tests that simulate live receipts run only in pytest temporary directories. They are protocol simulations, not authenticated access evidence. The current ignored live-smoke preflight manifest contains no responses or verification receipt. The earlier blocked paid-model preflight is also preserved separately and cannot satisfy the new model hash.

## Repository and zero-cost workflow

Private repository: https://github.com/Omore03/nlp-multilingual-reasoning, branch `main`. The initial implementation and handoff commits were pushed and remote hashes verified. The free-only revision updates configuration, adapter safeguards, tests and documentation; publication is checked in the delivery response. No secrets, environment, PDFs, weights, temporary renders or fabricated production data/results are published.

Historical hosted Actions runs returned `startup_failure` before jobs existed, with no logs (runs 43266675790 and 43266979025). **Hosted automation is now removed**, so this project does not depend on paid runner time or a CI repair. Local tests are the required merge check. Repository visibility and account billing settings were not changed.

## Remaining real integration

Supply a free OpenRouter API key without buying credits; run four-condition free smoke and inspect Urdu/English outputs before freezing the model. Obtain Hussain's reviewed 20-demo/10-dev data, validator and provenance; Rayyan's real selectors/tests/encoder and cache identity; and Saad's evaluation implementation. Complete the genuine pilot across available free daily quota windows, preserving configuration between days. Instructor access, later full-study deliverables and final submission remain pending.
