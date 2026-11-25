# Team handoff status

Updated 25 November 2026. The supplied modules and reviewed data are now integrated.

| Owner | Received and integrated |
| --- | --- |
| Hussain | Data generator/validator evidence, source/license notes and review document. His confirmation reported by Ammar approves all items except demos 4 and 5 |
| Rayyan | Production random/similarity selectors, 55 original tests, the 24 November encoder cache, pinned revision, 20 original selections and retrieval examples |
| Saad | Parser, metrics, report module, 77 original tests, fixtures and evaluation plan |
| Ammar | Prompting/inference framework, thin selector adapter, approval ledger, integration checks, real-run collection and report assembly |

## Review decisions

The Word form has 22 explicit accurate decisions, two correction requests and six unticked entries. Ammar's 25 November message reports Hussain's confirmation for the remaining entries. This later evidence is recorded separately; no missing signature date is invented.

The production pool has 18 approved demos and the dev set has 10 questions. Demos 4 and 5 remain false in `data/review/excluded_demos.jsonl`. The full ledger is `data/review/review_receipt.json`.

## Selection reconciliation

The older context handoff says the encoder run had not happened. The 24 November archive supersedes it: the cache covers all 30 questions, and all 20 original pairs were reproduced from its genuine vectors. Four pairs used unapproved demos. Removing those candidates changes 12 ordered selections, so the entire approved plan was regenerated.

The new `data/selection/approved_plan.json` identifies the encoder revision, cache hash, exact input files and query hashes. The adapter rejects changed questions or pools. It is real cached selection, not a synthetic test table. The small supplied vector cache and frozen selections are tracked; model weights stay outside Git.

## Evaluation fixes

The parser now accepts `FINAL_ANSWER:`. Real scoring requires a matching manifest and rejects mixed runs/models, mock input and duplicate successes. Empty or conflicting runs cannot be declared complete. Original tests are retained, with fixture-mode CLI calls made explicit.

## Remaining research work

The 80-configuration real pilot is complete and scored: both selectors reach 40/40 numerical matches, with zero parse failures. The report and baseline table are ready for team review. This ten-question pilot cannot establish strategy superiority. Final MGSM evaluation, larger data, additional selectors and four-shot prompting remain later work. See the [verification record](verification.md).

## Local baseline follow-up, 25 November 2026

The isolated `codex/baseline-submission-2026-11-25` branch integrates Rayyan's supplied delta. Seven saved runs and 380 scored records have been independently reconciled; see the root README and completion report for the current status. This does not change or replace the original 31B journal/report. 4B/1B local inference is inherited evidence, not a new execution on Ammar's Mac. The Google zero-shot attempt has zero successful responses because of capacity failures. No remote write or submission occurred.

## Publication update

The current baseline is published on `intermediate-stage`. The project lead has removed further internal approval requirements. Use the current README, consolidated report and submission checklist. Earlier pre-publication status notes above are historical. The error-tag worksheet remains draft; no independent reviewer signature is asserted.
