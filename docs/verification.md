# Executed engineering verification - direct Google revision

Date: 12 November 2026 (PKT). The user selected direct Google AI Studio and requires zero additional project spending. No billing changes, paid services, compute rental or subscription were made.

## Current executed checks

| Check | Actual outcome |
| --- | --- |
| `python -m pytest -q` | **90 passed**, fully offline |
| Native Google REST payload | Correct model/endpoint, user text parts, generationConfig, key in header; no query key, tools, OpenRouter fields or fallback |
| Native visible response/token/version metadata | Passed; separate thought parts excluded; no dollar cost fabricated |
| Wrong model/endpoint/credentials/paid fallback | Rejected by configuration/policy checks |
| Missing key or free-project confirmation | Blocks backend creation before any network operation |
| Model metadata preflight | Wrong identity/method/output capacity stops before inference |
| Native HTTP errors and structured retries | Sanitized terminal/transient behavior and RetryInfo honored |
| Google daily quota | Stops without repeat attempts or the remaining matrix calls |
| Direct receipt simulation, pacing, budget and resume | Passed offline using HTTPX MockTransport and injected clocks |
| Mock preview | 8 UTF-8 prompt records, one question/two fixture labels/four conditions |
| Four-condition mock smoke | 4 successful deterministic mock records |
| Full mock matrix | 80 unique successful mock records; no failures |
| Matrix resume | 0 new successes; existing matrix byte-for-byte unchanged |
| Authenticated direct Google live smoke | Four successful conditions in five generation attempts; zero terminal failures |
| Live resume and pilot receipt | Zero new requests, unchanged output bytes, receipt matches pilot settings |

The remaining suite retains prompt language/order/completeness, target-gold exclusion, selector boundary, ID/schema separation, UTF-8, required metadata, retry/failure, locks, incompatible-run and explicit tail-recovery checks. Historical OpenRouter free-only tests remain, but that adapter is not the active pilot route or an automatic fallback.

Current synthetic/mock artifacts: `results/mock/google_direct_preview.jsonl`, `results/mock/google_direct_smoke.jsonl`, `results/mock/google_direct_matrix.jsonl` and adjacent smoke/matrix manifests. The filenames identify the implementation revision; **the backend is still mock**, and these are not actual Google responses or research results.

Current matrix SHA-256, unchanged after no-op resume:

```text
6a7723b4bd51f826bcc1520b9cf21d37667ad1d7f953a78f23b812fcc9ff3fc2
```

Earlier mock runs/manifests remain untouched under their original names. The initial implementation had 51 passing tests and passed a clean local clone with standard venv/pip setup and mock matrix/resume. The OpenRouter free-only revision had 66 passing tests. Those historical checks do not establish authenticated native Google access.

## Live status

Direct Google credentials are stored only in ignored `.env`. The user confirmed Free tier and no attached billing account before calls. **All four direct conditions succeeded** on the synthetic fixture: U-U-U, U-U-E, U-E-E and E-E-E. Five generation attempts were used; all four final rows succeeded. Returned model `gemma-4-31b-it`, model metadata version `001`, input limit 262144, output limit 32768. Successful usage totals: 922 prompt + 192 completion = 1114 tokens. Google does not report measured dollar cost here, so none is fabricated; the model is documented free-only and no paid fallback/billing change was used.

The responses were inspected for worked solutions, Urdu UTF-8 and terminal `FINAL_ANSWER:` formatting, without adding Saad's parser/metrics or research grading fields. They are real hosted outputs to **synthetic** questions, not an integrated research pilot or Urdu quality certification. The genuine journal, manifest and freeze receipt are committed selectively after secret/provenance review under `results/live_smoke/google_direct/`. The receipt matches the active pilot model hash.

A live resume added zero records, made zero new requests, and left the four-row journal byte-for-byte unchanged. Live journal SHA-256: `61495daddeb16955910167c95e74a1806193d2522e8e7ae3f8a654691b04e5ec`. Sanitized evidence is in `docs/google_live_access_check.json`. The local project confirmation is explicitly user-provided, not an independent Cloud Billing audit.
The earlier OpenRouter account/key was authenticated and reported zero usage, a zero spending limit and all 50 daily free requests remaining. Six inference attempts returned upstream shared-pool HTTP 429, with no successful completion. Its sanitized historical evidence remains in `docs/live_access_check.json`; no credential value is recorded. Active direct Google output/receipt live under `results/live_smoke/google_direct/`, separate from those prior attempts.

## Publication and workflow

Private repository: https://github.com/Omore03/nlp-multilingual-reasoning, branch `main`. Earlier implementation/free-only handoff commits were pushed with matching remote hashes. Direct-route publication is checked in the delivery response. No secrets, environments, PDFs, weights, temporary renders or fabricated production data/results are published.

Hosted Actions automation remains removed under the zero-cost requirement; local tests are the merge check. Historical startup-failed CI runs are not an active dependency. Repository visibility and account billing settings are unchanged.

## Remaining real integration

Direct key/project confirmation, four-condition smoke and model freeze are complete. Integrate Hussain's reviewed 20-demo/10-dev package, validator and provenance; Rayyan's real selectors/tests/encoder/cache identity; and Saad's evaluation. Complete the genuine 80-record pilot using actual Google project quota, preserving settings across quota windows. Instructor access, later full-study deliverables and final submission remain pending.
