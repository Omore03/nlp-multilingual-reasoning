# Parser change proposal: version 2 (25 November 2026)

**Status: implemented on the local branch `local/ollama-gemma3-1b`, pending Saad's approval.** Proposed by Rayyan. The evaluation plan freezes the parser after the pilot and requires any change to be applied to
every configuration, re-scored from the raw files and logged. This document is that log.

## Problem

Two formatting patterns made mathematically correct answers score as wrong. Both appeared only in Gemma 3 4B output.

1. **No colon.** `FINAL_ANSWER 70` did not match the marker `FINAL_ANSWER\s*:`, so the answer was "missing".
2. **Generic marker before a restated question.** The model wrote "…final answer:", restated the question (e.g. "Hans has
   10 floors…"), and ended with a single correct `FINAL_ANSWER: 90`. The generic marker `final\s+answer\s*:` read the
   restated question's first number (10) as a second answer, so the response was "ambiguous: markers disagree: 10, 90".

Across all seven runs, 15 answers were affected (10 by pattern 2, 5 by pattern 1). In every one, the model's own working
reaches the gold number immediately before its final `FINAL_ANSWER`.

Checked and **not** a problem: "The final answer is 70." parses correctly; Urdu (۰–۹) and Arabic-Indic (٠–٩) digits,
thousands separators and bold markers already parse correctly.

## Rule (version 2)

1. If the response contains a literal `FINAL_ANSWER` (case-insensitive, colon `:`/`：` optional) **followed by a number**,
   the **last** such marker decides. One number → `ok`; several different numbers after it → `ambiguous`.
   A `FINAL_ANSWER` with no number after it (e.g. an echoed instruction "…marker FINAL_ANSWER: followed by the number") is
   skipped.
2. Otherwise the earlier rule applies unchanged: every default marker (`FINAL_ANSWER:`, `####`, "final answer:/is",
   `حتمی جواب:`, `آخری جواب:`) must agree on one number.
3. Where rules 1 and 2 give the same answer, the earlier result (including its `parse_detail` text) is returned unchanged.
4. Custom markers (`--marker`) switch rule 1 off, so custom markers still fully replace the defaults.

Why keep the fallback: 37 Gemma 3 1B answers contain only "Final Answer: The final answer is 70." with no `FINAL_ANSWER`;
removing the generic marker would turn some of them from correct to missing.

Code: `src/evaluation/answer_parser.py` (`PARSER_VERSION = "2-last-final-answer-first"`, `PRIMARY_MARKER`,
`_last_primary`, `parse_answer(response, markers, primary)`; the old body is now `_parse_markers`, unchanged).
Tests: 12 new cases in `tests/test_evaluation.py` (no colon, full-width colon, Urdu digits, restated question, last marker
wins, echoed instruction skipped, all-agree unchanged, fallback cases, several numbers → ambiguous, custom markers). All
existing evaluation tests pass unchanged; the full suite is 273 tests.

## Effect (same raw responses, re-scored)

| Run | Correct before | Correct after | Gained | Lost | Parse failures before → after |
|---|---|---|---|---|---|
| Gemma 4 31B two-shot | 80/80 | 80/80 | 0 | 0 | 0 → 0 |
| Gemma 3 4B two-shot | 61/80 | 64/80 | 3 | 0 | 7 → 1 |
| Gemma 3 4B zero-shot | 14/30 | 23/30 | 9 | 0 | 13 → 1 |
| Gemma 3 4B random, seed 43 | 29/40 | 30/40 | 1 | 0 | 1 → 0 |
| Gemma 3 4B random, seed 44 | 30/40 | 32/40 | 2 | 0 | 3 → 0 |
| Gemma 3 1B two-shot | 16/80 | 16/80 | 0 | 0 | 15 → 15 |
| Gemma 3 1B zero-shot | 7/30 | 7/30 | 0 | 0 | 11 → 11 |

- **No answer lost a correct score.** The 31B scored files are byte-identical after re-scoring.
- 7 further 4B records move from "ambiguous/missing" to a parsed **wrong** number (e.g. 176 or 256 where the gold is
  216): these were real arithmetic errors hidden as format failures, and are now counted as reasoning errors.
- One 1B record stays ambiguous with a new detail text ("several numbers after the last FINAL_ANSWER marker").

## What changes in the conclusions

- 4B two-shot: random 31/40 (selection seeds 42/43/44: 31, 30, 32), similarity 33/40. Still no established strategy
  difference (only U-U-U differs: 3–0, exact McNemar p = 0.25).
- 4B zero-shot rises to 23/30. Compare it with the same question/instruction conditions in two-shot results; the different aggregate denominators do not establish that examples mainly teach formatting.
- 1B and 31B conclusions are unchanged.

## Files

- Pre-change scored files are kept next to each run in `results/<run>/scored_before_parser_fix/` (evaluated records,
  summaries, reconciliation, error breakdown). Raw responses were not touched; no model was called again.
- Regenerated after the change: every run's evaluated/summary/reconciliation/error-breakdown files,
  `docs/model_comparison.md` (with a before/after section), `results/error_tagging/` (now 32 rows), and the Gemma 3 4B and
  1B reports (method sentence updated; still 2 pages). The original 31B report is unchanged.

## To approve

- [ ] Saad: review `src/evaluation/answer_parser.py` and the 12 new tests.
- [ ] Saad: spot-check the 15 changed answers (list: `docs/model_comparison.md`, "Parser change" section; each run's
      `scored_before_parser_fix/pilot_evaluated.jsonl` vs `pilot_evaluated.jsonl`, matched by `record_id`).
- [ ] Team: agree that version 2 is the official parser for all later runs (40-question dev, MGSM).
- [ ] Optional: record `PARSER_VERSION` in `pilot_reconciliation.json` (one line in `src/evaluation/report.py`; not done
      here so the team's 31B files stay byte-identical).

## To reject

Restore `src/evaluation/answer_parser.py` and `tests/test_evaluation.py` from `main`, then copy each run's
`scored_before_parser_fix/*` files back into the run folder (or re-score with the README command). No raw data changes.

## Independent integration audit, 25 November 2026

All 380 records were rescored and matched to both supplied score versions. Fifteen correct answers are recovered (ten generic-restatement cases, five missing colons); none are lost. **Seven**, not six, additional answers become parsed wrong: three in 4B main, three in 4B zero-shot and one in seed 44. See `evidence/baseline_2026_11_25/parser_changes.csv`.

Version `2.1-bounded-final-answer-first` adds word boundaries around the literal marker, preventing embedded identifiers such as `NOT_FINAL_ANSWER` from being treated as terminal markers. All 380 supplied v2 prediction/status/detail rows remain identical. Twelve additional integration regressions cover marker boundaries, signed Urdu decimals, echoed markers, trailing calculations and stale/mismatched analysis files; the full suite has 285 passing tests. New reconciliation outputs record parser version, parser hash, marker patterns and evaluated-file hash under `results/verified/`. Archived outputs are unchanged.

Each of the 15 numerical gains was inspected. One soda response (`b297d57f...`, seed 44) gives the correct number while reversing money spent and money remaining in its prose. Numerical matching does not certify the full reasoning. Human approval remains pending; the draft review does not impersonate Saad.
