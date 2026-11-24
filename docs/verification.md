# Verification

Updated 25 November 2026 (PKT). Real results and engineering checks are separate.

## Integrated checks

| Check | Outcome |
| --- | --- |
| Offline suite, including a fresh GitHub clone | 229 passed |
| Approved data | 18 demos, 10 dev, two excluded demos; 30 disjoint IDs |
| Arithmetic and review ledger | Passed |
| Pinned GSM8K source | All 30 questions and keys match; five questions use normalized whitespace |
| Original Rayyan selections | All 20 reproduced from genuine vectors |
| Approved frozen selections | 20 pairs regenerated; no rejected IDs; byte-identical regeneration |
| Real prompt preview | Eight prompts inspected; target gold excluded |
| Integrated mock matrix | 80 successes; resume adds zero records |

The mock matrix and manifest are preserved in `results/mock/integrated_matrix.*`. They are engineering fixtures and never enter research accuracy.

## Real pilot

**Incomplete: 61/80 unique successful responses.** The data consist of 10 questions, two strategies and four language conditions, with two examples per prompt.

- Correct numerical answers among scored responses: 61/61.
- Parse failures: 0.
- Unsuccessful entries retained in history (including local budget deferrals): 29.
- Missing configurations: 19.
- Reconciliation balanced: true; matching real manifest required.
- Run identity: `a6a5824eab93553910ed95576e6853d85096195cbdae4fab4e9d9bede68246dc`.
- Journal SHA-256: `33b0c824a341f7b1fe8f43d520998ad20829f524c5beb39cec676802afc8ba8c`.
- Manifest SHA-256: `2820d4c167c2dc3a830382dded0ec11ec08e9795d782ada9865716e347fa3aab`.

The final table is [pilot_summary.md](../results/pilot_summary.md). The full journal, manifest, evaluated responses and reconciliation are tracked separately. Failures followed by success count once; failed calls are not model answers.

Recorded terminal error codes: `free_request_budget_exhausted`: 1, `http_503`: 28.

Collection is dated 25 November, after the TA's 23 November deadline. Partial coverage does not establish a complete baseline; even complete coverage is only a small development pilot, not final benchmark performance.

## Model and spending constraint

The configured native Google model is `gemma-4-31b-it`, with the frozen settings in `configs/pilot.yaml`. Requests use the existing project that the user confirmed as Free tier with no billing attached. No paid fallback or billing change was made. The API does not provide measured dollar cost, so no billing measurement is claimed.

Successful-response token metadata: `{"completion_tokens": 7310, "prompt_tokens": 23878, "total_tokens": 31188}`. Failed requests may not report usage; these totals are not a complete account of all provider-side computation.

The four-condition synthetic live smoke from 12 November remains historical access evidence under `results/live_smoke/google_direct/`. Its journal SHA-256 is `61495daddeb16955910167c95e74a1806193d2522e8e7ae3f8a654691b04e5ec`. It is not included in research metrics. The dated model-catalog snapshot also remains historical.

## Submission and later work

The report uses the actual IEEEtran class; its rendered page count must stay within three including references. Upload and meeting attendance remain team actions. The repo is public as observed on 25 November; this work does not change visibility. Hosted CI remains disabled.

Correct/re-review the two excluded demos before reuse. Larger reviewed experiments, deferred selectors, four-shot prompting and separate MGSM evaluation remain future work. See [submission checklist](submission_checklist.md).
