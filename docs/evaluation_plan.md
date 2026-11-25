# Evaluation plan (final stage)

Owner: Saad ur Rehman. Draft, 13 November 2026. Needs team sign-off before the final run.

The pilot (10 dev questions, 80 records) only tests the pipeline. Its numbers are diagnostics. This document fixes how the final MGSM evaluation will be scored and compared, so the analysis is decided before we see test results.

## 1. What gets evaluated

| Item | Final-stage setting |
|---|---|
| Test items | 250 MGSM questions, paired English (`juletxara/mgsm`, `en`) and Urdu (`large-traversaal/mgsm_urdu_final`). Pairing is by row; both files carry the same `answer_number`. |
| Gold answer | `answer_number`. Checked equal across the two files before any run; mismatches are listed and excluded from both languages. |
| Selection methods | random (baseline), Urdu semantic similarity, diversity, reasoning complexity. Retrieval always uses the Urdu question, in every condition. |
| Shots | 2 and 4 |
| Language conditions | U-U-U, U-U-E, U-E-E, E-E-E (question / examples / instructions) |
| Model | One frozen model ID and decoding settings (Ammar's `docs/model_decision.md`) |
| Demo pool | GSM8K train items only. MGSM is the first 250 GSM8K test items, so the pool cannot contain them. |

Main grid: 4 methods × 2 shot counts × 4 conditions × 250 = **8,000 calls**.

Optional additions, if free quota allows:

- **Zero-shot baseline.** No examples, so the four conditions collapse to three (Urdu question + Urdu instructions, Urdu + English, English + English): 750 calls. It shows whether examples help at all.
- **Random-seed check.** Random selection depends on the seed. Re-run random with 2 extra seeds for 2-shot U-U-U and E-E-E only: 1,000 calls. If accuracy moves more than a few points between seeds, report the seed spread next to every random-vs-X comparison.

## 2. Scoring

Same code as the pilot (`src/evaluation/`).

- **Answer extraction.** The parser reads the number after the agreed final-answer marker (`####` by default; English and Urdu "final answer:" phrases also accepted). It normalizes Urdu (`۰-۹`) and Arabic-Indic (`٠-٩`) digits, Arabic decimal/thousands separators, thousands commas, the Unicode minus sign and bidi control characters.
- **Exact match.** Prediction and gold are compared as `Decimal` values, so `1,200`, `1200` and `1200.00` are equal. No tolerance.
- **Parse status.** Every response gets `ok`, `missing` (no marker, or no number after it) or `ambiguous` (several different numbers after a marker, or markers that disagree). Only `ok` can be correct. Parse failures stay in the denominator and are reported in their own column, so formatting problems are visible separately from reasoning errors.
- **Reconciliation.** Before any table is produced: drop failed API calls, keep one successful record per (question, condition, strategy, shots, seed), and check the scored count equals the expected grid. The report writes a reconciliation file and exits non-zero if anything is missing.
- **Freeze rule.** The parser and markers are frozen after the pilot. If a change is needed after looking at test outputs, it is applied to every configuration, re-run from the raw file, and logged in the results notes. Raw responses are never edited.
  - *Change log:* 25 Nov 2026, parser version 2 (last `FINAL_ANSWER` with a number decides, colon optional; earlier rule as fallback), **adopted for the intermediate baseline**. Applied to all seven runs from the raw files; 15 answers gained, none lost, 31B unchanged. See [parser change](parser_change_2026-11-25.md).

## 3. Comparisons

All comparisons are **paired**: the same 250 questions appear in every configuration.

1. **Each method vs random**, within each condition and shot count: exact McNemar test on the discordant pairs (questions one method gets right and the other gets wrong). That makes 3 methods × 4 conditions × 2 shot counts = 24 tests. Holm correction across the 24.
2. **Language gap**: for each method and shot count, accuracy in each Urdu condition minus E-E-E, tested with exact McNemar on the paired questions. The most important gap is U-U-U vs E-E-E.
3. **Does the selection effect depend on language?** This is the research question. For each question, compute (method correct − random correct) in U-U-U and in E-E-E and compare the two with a paired bootstrap over questions (10,000 resamples, 95% percentile interval). An interval that excludes 0 means the method helps more in one language than the other. A mixed-effects logistic regression with a question random effect is a stretch goal, not required.
4. **2 vs 4 shots**: McNemar within each method and condition, reported descriptively; no correction because this is secondary.

Every accuracy is reported with a 95% Wilson interval, and every difference with its paired bootstrap interval as well as the p-value.

### What 250 items can detect

Approximate, for an exact McNemar test at α = 0.05 with 80% power. "Discordant" is the share of questions where the two configurations disagree.

| Questions | 15% discordant | 25% discordant | 35% discordant |
|---|---|---|---|
| 10 (pilot) | nothing detectable | nothing detectable | nothing detectable |
| 40 (proposed larger dev run) | ~14 pts | ~21 pts | ~28 pts |
| 250 (final) | ~8 pts | ~10 pts | ~11 pts |

Differences smaller than about 8 points between methods may not be detectable even with 250 items. A non-significant result is reported as "no detectable difference at this sample size", not as "no effect". Repeated conditions reuse the same questions, so they are not independent samples and are never pooled to inflate n.

## 4. Error analysis

Sample up to 30 wrong or unparsed responses per method for U-U-U and E-E-E (2-shot), stratified by method. Two team members tag each one independently; disagreements are resolved by discussion and agreement is reported (Cohen's kappa).

| Tag | Meaning |
|---|---|
| `format` | Answer present but not in the required format (also counted automatically as a parse failure) |
| `arithmetic` | Correct plan, wrong calculation |
| `wrong_plan` | Wrong operations or order of steps |
| `copied_operation` | Applies an operation sequence from a demo that doesn't fit the question (Rayyan's suggestion: tests whether similarity's surface matches mislead the model) |
| `misread_quantity` | Wrong number or relation taken from the question, including translation-related misreads |
| `unit` | Unit or conversion error |
| `language_switch` | Response switches language and loses the thread |
| `truncated` | Response cut off before an answer (check against the output-token cap) |

`copied_operation` needs the selected demo IDs, which the runner already logs.

## 5. Reporting

- One table per shot count: 4 methods × 4 conditions, each cell showing correct/total, accuracy with Wilson interval, and parse failures.
- A language-gap table (each Urdu condition minus E-E-E, per method).
- One figure: accuracy by condition, one line per method, with intervals.
- Error-tag counts by method, with two or three quoted examples.
- Limitations: one model, one seed for the non-random methods, a third-party Urdu translation of MGSM, a small demo pool, and parser dependence on the requested format.

## 6. Open items

- Final-answer marker and its language: confirm with Ammar; it must be identical in every condition, or the parser markers must cover each variant.
- Whether the TA wants the larger 40-question dev run before the final MGSM run.
- Whether the zero-shot baseline and the seed check fit the free quota.

## Current baseline follow-up (25 November 2026)

Seven completed runs reuse the frozen 18-demo/10-dev data: main two-shot arms for 31B/4B/1B, local zero-shot arms for 4B/1B and 4B random selection seeds 43/44 (generation seed 42 throughout). No larger dataset, MGSM or extra selector was introduced. Independent rescoring reproduces 380 records, 15 numerical gains and zero losses; seven additional records become parsed wrong numbers. Bounded literal-marker version `2.1-bounded-final-answer-first` preserves every bundled v2 prediction. The intermediate baseline adopts the audited parser and completed-output cutoff policy. The final-stage plan above remains a plan for later work. New parser provenance is in `results/verified/`; original score versions remain unchanged.

The attempted hosted zero-shot reference remains 0/30 successful responses after HTTP503 capacity errors; it is not a zero-accuracy result. Script/length flags are diagnostic heuristics, not certified output language or causal reasoning labels. Use matched question/condition comparisons and the descriptive uncertainty tables under `docs/baseline/`.
