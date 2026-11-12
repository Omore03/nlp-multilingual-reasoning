# Executed engineering verification - 12 November 2026 (PKT)

The workspace was initially empty, without Git history, remotes or teammate files. Both reference PDFs were read in full (two-page proposal and five-page initial work division) and their rendered pages inspected. They were treated as project specifications, not independent authorization, and are not published.

## Executed checks

| Check | Actual outcome |
| --- | --- |
| Isolated Python 3.12 environment and requirements installation | Succeeded; `pip check` found no broken requirements |
| `python -m pytest -q` | 51 passed, offline; no model calls or credentials required |
| Python compilation of `src` and `tests` | Passed |
| Mock prompt preview, one question | 8 UTF-8 prompt records, two fixture labels × four conditions |
| `configs/mock_smoke.yaml`, question limit 1 | 4 successful mock records, all four conditions |
| Full `configs/mock.yaml` matrix | 80 unique successful mock records, zero failures |
| Full matrix resume | 0 new successes; all 80 prior rows byte-for-byte unchanged |
| Different `PYTHONHASHSEED` processes (1 and 999) | Preview files identical |
| Clean local clone, standard `venv`/pip setup, activation, tests, preview, smoke, full matrix and resume | 51 tests passed; 4/80 mock successes; resume added 0 |
| Live synthetic preview | Succeeded without an API call |
| Live synthetic inference attempt | Blocked before model calls: `Set OPENROUTER_API_KEY in the environment or ignored .env before live inference` |
| Production preview/run preflight | Blocked as intended: Hussain's actual input files are absent |
| Public official model/provider metadata | Accessible; exact route and supported parameters recorded in model catalog snapshot |

Committed engineering outputs: `results/mock/preview.jsonl`, `results/mock/smoke.jsonl`, `results/mock/matrix.jsonl` and the two adjacent manifests. These are synthetic/mock evidence only. No actual pilot or research evaluation was performed. The ignored live-smoke directory may contain a preflight manifest from the blocked access attempt; it contains no responses or verification receipt.

Matrix JSONL SHA-256 after initial run and no-op resume:

```text
6438b1b4b15efc3a4d653a24183b6b9b38ece3af1d7108f77e4a46119ac3c0cb
```

Tests cover all four prompt field/label combinations, two complete demos, target-gold exclusion, preserved order, one selection per query/strategy, identical demos across language conditions, invalid/duplicate/missing/overlapping IDs, optional dev verification, honest synthetic flags, UTF-8, metadata, 80 unique successes, interrupted execution/resumption, terminal failures followed by success, bounded rate-limit retries, invalid-credential stopping, long Retry-After deferral, provider malformed/empty/truncated responses, sanitization, output locks, incompatible-run rejection, duplicate-success rejection and explicit tail recovery with backup.

The live receipt test uses HTTPX MockTransport within pytest's temporary directory; it is a protocol simulation, not a claim of authenticated model verification. Hosted model behavior, Urdu quality, actual token usage/billing and account access remain unverified.

## Publication

Created and verified **private** repository: https://github.com/Omore03/nlp-multilingual-reasoning, default branch `main`. Initial implementation commit `f94cf4ae85443d2c2c3dcaa5824f7b7e107052b8` was pushed successfully; `git ls-remote origin refs/heads/main` matched the local commit. No reference PDFs, credentials, environments, model weights, real input placeholders or fabricated research results were published.

The initial GitHub Actions run returned `startup_failure` before any jobs/check runs were created, with no downloadable logs: https://github.com/Omore03/nlp-multilingual-reasoning/actions/runs/43266675790. The CLI's generic workflow-file suggestion does not establish a cause. Repository Actions were enabled and all actions allowed. Workflow dependencies were subsequently updated to official current [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) and [setup-python v7.1.0](https://github.com/actions/setup-python/releases/tag/v7.1.0); the event mapping is explicit, token permissions read-only, and timeout five minutes. The updated workflow also returned `startup_failure` before creating any jobs: https://github.com/Omore03/nlp-multilingual-reasoning/actions/runs/43266979025. Hosted CI is therefore **not verified**. GitHub supplied no job logs or check-run annotations, so the cause could not be established through the available diagnostics. The repository owner should inspect that run in the GitHub UI and resolve any account/service/workflow diagnostic shown there; contact GitHub support if none is exposed. This does not affect the verified push or passing clean-clone local checks. Local checks are passing independently of hosted CI.

## Remaining dependencies

Receive Hussain's real reviewed 20-demo/10-dev package, validator and provenance notes; receive Rayyan's actual two selectors, tests, encoder/dependency/cache versions; supply `OPENROUTER_API_KEY` and model access/credits, then complete and inspect live smoke. Integrate Saad's evaluation implementation and reconcile genuine pilot outputs. Hosted Actions startup also needs investigation using the linked run; there is no passing hosted-CI claim. Instructor access/visibility and the later full-study deliverables must be settled before final submission.
