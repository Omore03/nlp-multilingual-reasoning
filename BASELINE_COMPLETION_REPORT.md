# Baseline completion report

25 November 2026, Asia/Karachi. Prepared for Ammar and the team; no remote integration or submission performed.

## Local branch and exact checkpoints

- Worktree: `/Users/ammar/Desktop/NLP/baseline-submission-2026-11-25`.
- Branch: `codex/baseline-submission-2026-11-25`.
- Fetched base and unchanged local/remote main: `01f52473ba2966d68f0b6a561ca348d9006d9484`.
- Exact 35-file bundle import commit: `b6dde3edc0600ecc05b2ffe97105832985c7f776`.
- Verified implementation checkpoint: `d85e2aa3f36b500da6ab761d5564fcf6f3104ba7`.
- **Final reviewed code/evidence SHA: `d05d2a993b390d5e68680afd14cdb657d2cc23d5`**, including the clean-checkout packaging correction.
- This report and final verification notes are recorded in a subsequent documentation-only checkpoint. The packaged copy appends the exact final branch-head SHA after committing; `REVIEW_RELEASE.json` records that SHA as well.

The original workspace remains on main. Its pre-existing untracked `NLP_Team_Action_Plan_23_Nov_2026.pdf` was not moved, staged or changed. No stash, reset, history rewrite, main commit, push, PR, merge, deployment or submission occurred.

## Inputs and integration

Rayyan's ZIP SHA-256 is `3ebd3a2531adc8cd3d26a28fd829068c0b51dc7670f7dfe5235f8660c05baded`. All 181 checksum entries passed after safe extraction outside the repository. The fetched base exactly matched the patch base; `git apply --check` passed and the patch was applied once. All 35 initial paths matched the supplied source bytes, including binary PDFs. IEEE vendor whitespace was preserved, not reformatted.

All seven completed journals, manifests, supplied v2 outputs and `scored_before_parser_fix/` outputs are retained. The bundle's nested folders were mapped to the flat paths already used by its configs/scripts. The stopped six-row 1B attempt and synthetic smoke receipts remain separate and are not scored as research data. A clean clone caught two omitted root 31B breakdown files; both were added and the complete clean audit then passed. All 107 receipt-referenced files are now tracked.

The approved 18-demo/10-dev inputs, genuine cached vectors, original 31B raw/scored journal and original IEEE report are unchanged. The optional synthetic dev40 set was not used. MGSM, dataset expansion, diversity/complexity, four-shot and generalized larger grids were not implemented.

## Changes and rationale

- Integrated Ollama backend, nine configs, zero-shot templates, runner support, seed checks, tests and analysis from Rayyan.
- Hardened literal marker boundaries: identifiers such as `NOT_FINAL_ANSWER` are not terminal markers. Version `2.1-bounded-final-answer-first` leaves all 380 supplied v2 scored rows identical.
- New evaluations record parser version, parser hash, marker patterns and evaluated-file hash. Archived originals stay unchanged under their original provenance.
- Analysis/report builders reject stale artifact hashes; paired comparisons reject different or repeated question IDs. The legacy report builder is explicitly restricted to its supported two-shot matrix.
- Added offline audit, matched statistics, a consolidated report builder and a local-only packaging script. Raw results are never overwritten; verified rescoring goes under `results/verified/`.
- Simplified README/run/checklist documentation and expanded the individual-contribution table.
- Prepared a consolidated two-page IEEE report and 32 draft error tags. Human reviewer/sign-off fields remain blank/pending.

## Independently reconciled scores

Every row is a complete saved run; failed entries are distinct from completed responses. Ten distinct questions are reused across all runs.

| Run | Scored | Correct v1 | Correct v2/current | Parse failures current | Output cutoffs |
|---|---|---|---|---|---|
| 31B two-shot | 80 | 80 | 80 | 0 | 0 |
| 4B two-shot | 80 | 61 | 64 | 1 | 1 |
| 4B zero-shot | 30 | 14 | 23 | 1 | 0 |
| 4B random seed 43 | 40 | 29 | 30 | 0 | 0 |
| 4B random seed 44 | 40 | 30 | 32 | 0 | 0 |
| 1B two-shot | 80 | 16 | 16 | 15 | 14 |
| 1B zero-shot | 30 | 7 | 7 | 11 | 10 |

Total: **380 scored configurations**, not 380 independent questions. All run identities, plan/record/prompt hashes, frozen inputs, approved-only selection, correct language templates, returned model IDs and local digests passed. The original 35 HTTP503 entries plus one local deferral in the 31B journal remain preserved.

All 15 recovered correct responses were inspected: ten generic-marker/restatement cases and five missing-colon cases; zero losses. **Seven**, not the handoff's six, additional 4B outputs become parsed wrong (three main, three zero-shot, one seed 44). The changed-record CSV includes exact record IDs and full responses. A seed-44 soda response has a correct final 6 but reverses spent/remaining amounts in its prose: numerical matching does not certify all working.

4B similarity scores 33/40; random seeds 42/43/44 score 31/40, 30/40 and 32/40. In nominal U-U-U, similarity 9/10 versus random seed 42's 6/10 gives b=3, c=0, exact two-sided p=0.25; random seed 44 also scores 9/10. No statistically established selection advantage. Zero-shot aggregate 23/30 is not directly comparable to two-shot 31/40; matched cells and descriptive exact tests are supplied. Model size is confounded with generation, backend, quantization and options.

## Tests and reproduction actually executed

A separate fresh Python 3.12.12 environment installed the five declared pins; an additional clean local clone used its own fresh environment.

| Check | Actual result |
|---|---|
| `python -m pytest -q` | 285 passed, 0 failed/errors/skipped; also passed in clean clone |
| `python -m src.data.validate` | 18 approved demos, 10 dev, 2 exclusions, 30 unique/disjoint IDs; arithmetic passed |
| `python scripts/audit_baseline.py` | 380 records; all inherited hashes/plan identities; v1 and v2 reproduced; 15 gains, 0 losses |
| CLI preview for every `configs/*.yaml` | All 14 passed, without inference |
| Real-model verification receipts | All eight real configurations accepted matching inherited receipts |
| Frozen selection regeneration | Same approved-plan SHA `f7b5b5b264bf984a132d91be2bce2dd2b8e3a9ba902e8d7ec0ce503052bcc998` |
| Selection seed checks | Seed 42 reproduces all ten pairs; seeds 43 and 44 each change all ten |
| Mock run then resume | 80 successes, zero failures; resume adds zero records and leaves raw hash unchanged |
| `scripts/compare_arms.py`, `baseline_statistics.py`, `build_baseline_report.py` | Comparison, 24 per-cell Wilson intervals, 28 matched descriptive tests and table reproduced |
| Breakdown and blank worksheet reproduction | All seven CSV/Markdown breakdowns and original 32-row blank worksheet match byte-for-byte |
| Legacy report builder | Original 31B generated inputs reproduce without Git diff |
| Tectonic 0.17.0 | Consolidated report and both inherited small-model reports build; consolidated PDF is two pages including references |
| Visual review | Both consolidated pages inspected; no clipping/overlap/missing glyphs |
| Security | Candidate artifacts scanned against local secret values without printing them; no credentials found |

See `REPRODUCE_BASELINE.md` for commands and `evidence/baseline_2026_11_25/validation.json`, `clean_checkout.json` and `source_receipt.json` for evidence. The clean checkout regenerates the audit, comparison, statistics, new report table and original report inputs without a tracked diff.

## What was inherited and what was newly run

Rayyan collected the 4B/1B model generations on his Apple M5 using Ollama 0.40.18. Their raw output/digest/prompt evidence was independently checked and rescored here; **local inference was not repeated** because Ammar's Mac has neither Ollama nor a listening local server. No model weights were installed or downloaded. The original hosted 31B two-shot run remains unchanged.

The missing hosted 31B zero-shot arm was attempted with the existing private key, existing user-confirmed free project, fixed free Gemma model and unchanged policy guards. Google pricing was rechecked. Two terminal HTTP503 entries record six generation attempts; an in-flight call was cancelled when repeated capacity failure was clear. **Zero successful responses out of 30**; this is unavailable data, not 0% accuracy. The journal, manifest and sanitized attempt receipt remain separate. No billing change, paid fallback or automatic capacity-retry loop was used. The key does not independently audit project billing or future quota.

## Limitations and approvals

- All 18 nominal Urdu demo solutions contain English unit words. Data was kept frozen; translation edits need human review and a new experiment identity.
- Duplicate screening found no identical normalized English demo/dev question; maximum character similarity 0.4475. It is only a heuristic, not semantic or translation certification.
- Local totals stay below the 4096 context limit; returned token counts do not independently prove that no input was truncated. Unsent model/runtime defaults remain defaults.
- Completed local output cutoffs are scored as returned; this proposed policy and the parser change still need Saad/team ratification (D2/D3).
- Draft error tags do not assert that examples caused errors; low-confidence cases and absent derivations are marked for human review. Saad/Rayyan review remains pending.
- D1: agree the primary model (4B recommended). D6: agree the consolidated report/extra arms and team author review. No human approval is invented.
- D4 MGSM and D5 expansion are deferred. Pilot sufficiency, the latest TA deadline, actual upload and meeting attendance are team/TA matters.
- Ammar must approve before **any push, PR or main integration**. Current baseline engineering checks pass; the optional 31B reference and named human approvals remain open.

## Artifacts and recommended next action

`reports/baseline_2026_11_25/baseline_report.pdf` and complete IEEE source; unchanged original report; all seven raw/scored arms plus pre-fix archives; `results/verified/`; checksum/validation receipts; exact parser-change records; draft error tags; matched statistics; simplified README and exact reproduction commands.

After the final local documentation checkpoint, `python scripts/package_baseline.py` produces `output/review/NLP_Baseline_Review_2026-11-25.zip`, a binary-safe patch against the base, SHA-256 checksums, this report with the final branch-head SHA, and `REVIEW_RELEASE.json`. The package excludes secrets, Git internals, environments, model weights and runtime caches; the small genuine tracked vector file is deliberately included for reproducibility.

Review the local branch/package, obtain the listed human decisions, then authorize a specific remote action if desired. No remote or submission action is included in completion.
