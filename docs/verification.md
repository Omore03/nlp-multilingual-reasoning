# Verification record

Date: 12 November 2026 (PKT). Engineering checks are separate from research evaluation.

## Local checks

| Check | Outcome |
| --- | --- |
| Offline test suite | 90 passed |
| Mock prompt preview | Eight prompts: two fixture strategy labels × four conditions |
| Mock smoke | Four successful records |
| Full mock matrix | 80 unique successes, no failures |
| Matrix resume | Zero new successes; journal unchanged |
| Native Google adapter | Offline checks cover payloads, metadata, secrets, retries, quota limits and receipts |
| Runner and prompts | Checks cover languages, ordered demo reuse, gold exclusion, schema, UTF-8, logs, locks and recovery |

Committed mock evidence uses `results/mock/google_direct_preview.jsonl`, `google_direct_smoke.jsonl` and `google_direct_matrix.jsonl`, with adjacent manifests. These filenames identify the implementation revision; their backend is mock.

Matrix SHA-256: `6a7723b4bd51f826bcc1520b9cf21d37667ad1d7f953a78f23b812fcc9ff3fc2`.

The simplified README commands were rerun for this documentation update: 90 tests passed, preview produced eight prompts, smoke produced four successes and the matrix produced 80. Resume added no records and preserved the journal bytes. Local Markdown links and code blocks were also checked. The real preview still stops on missing reviewed production inputs, before inference.

## Authenticated live smoke

The direct Google run completed all four conditions on a synthetic question:

| Item | Recorded result |
| --- | --- |
| Model / metadata version | `gemma-4-31b-it` / `001` |
| Successful conditions | U-U-U, U-U-E, U-E-E, E-E-E |
| Generation attempts / terminal failures | 5 / 0 |
| Successful-response token usage | 922 prompt + 192 completion = 1114 |
| Resume | Zero new requests; journal unchanged |
| Model receipt | Matches the pilot model settings |

Visible solutions, Urdu text and final markers were inspected. This does not certify translation quality or research accuracy. No parser, accuracy metrics or research grading were added.

Evidence: [sanitized access check](google_live_access_check.json), [journal](../results/live_smoke/google_direct/smoke.jsonl), [manifest](../results/live_smoke/google_direct/smoke.manifest.json) and [receipt](../results/live_smoke/google_direct/model_verification.json).

Live journal SHA-256: `61495daddeb16955910167c95e74a1806193d2522e8e7ae3f8a654691b04e5ec`.

The existing journal hash and receipt's model hash were checked again against the pilot config during this documentation update. No new live calls were made.

The user confirmed an unbilled Free tier project. This is not an independent billing audit. The API did not supply measured dollar cost; none was invented. No paid fallback was used. Credentials remain in ignored `.env`.

## Current limits

Hussain's draft generator and Rayyan's selector package have arrived but are not integrated. Human review and the later selection artifacts need confirmation. Saad's evaluation and the real 80-record pilot remain pending. See [handoff status](handoff_status.md).

The repository is private at [Omore03/nlp-multilingual-reasoning](https://github.com/Omore03/nlp-multilingual-reasoning). Local tests are the merge check; hosted CI is disabled. Earlier mock runs and OpenRouter access failures are retained as historical evidence, with their original identities. They do not count as real pilot results.
