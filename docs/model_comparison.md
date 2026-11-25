# Model-arm comparison: Gemma 4 31B, Gemma 3 4B, Gemma 3 1B

Same 10 dev questions, 18-item pool, frozen selections, prompts and decoding in every two-shot arm; only the model changes. Zero-shot arms use the same questions with no demonstrations. Each cell is correct/10. Built by `scripts/compare_arms.py` from the evaluated files.

## Exact-match accuracy

| Arm | Strategy | U-U-U | U-U-E | U-E-E | E-E-E | All |
|---|---|---|---|---|---|---|
| Gemma 4 31B (two-shot) | random | 10/10 | 10/10 | 10/10 | 10/10 | 40/40 |
| Gemma 4 31B (two-shot) | similarity | 10/10 | 10/10 | 10/10 | 10/10 | 40/40 |
| Gemma 3 4B (two-shot) | random | 6/10 | 8/10 | 8/10 | 9/10 | 31/40 |
| Gemma 3 4B (two-shot) | similarity | 9/10 | 7/10 | 8/10 | 9/10 | 33/40 |
| Gemma 3 4B zero-shot | zero-shot | 8/10 | 7/10 | = U-U-E | 8/10 | 23/30 |
| Gemma 3 1B (two-shot) | random | 0/10 | 1/10 | 2/10 | 4/10 | 7/40 |
| Gemma 3 1B (two-shot) | similarity | 0/10 | 2/10 | 2/10 | 5/10 | 9/40 |
| Gemma 3 1B zero-shot | zero-shot | 1/10 | 2/10 | = U-U-E | 4/10 | 7/30 |

U-E-E is not run at zero shots: with no demonstrations its prompt is the same as U-U-E.

## Similarity minus random (paired)

b = questions only similarity solved; c = questions only random solved; p = exact two-sided McNemar.

| Arm | Condition | Similarity − random (points) | b | c | p |
|---|---|---|---|---|---|
| Gemma 4 31B (two-shot) | U-U-U | +0 | 0 | 0 | 1.000 |
| Gemma 4 31B (two-shot) | U-U-E | +0 | 0 | 0 | 1.000 |
| Gemma 4 31B (two-shot) | U-E-E | +0 | 0 | 0 | 1.000 |
| Gemma 4 31B (two-shot) | E-E-E | +0 | 0 | 0 | 1.000 |
| Gemma 3 4B (two-shot) | U-U-U | +30 | 3 | 0 | 0.250 |
| Gemma 3 4B (two-shot) | U-U-E | -10 | 0 | 1 | 1.000 |
| Gemma 3 4B (two-shot) | U-E-E | +0 | 0 | 0 | 1.000 |
| Gemma 3 4B (two-shot) | E-E-E | +0 | 0 | 0 | 1.000 |
| Gemma 3 1B (two-shot) | U-U-U | +0 | 0 | 0 | 1.000 |
| Gemma 3 1B (two-shot) | U-U-E | +10 | 1 | 0 | 1.000 |
| Gemma 3 1B (two-shot) | U-E-E | +0 | 1 | 1 | 1.000 |
| Gemma 3 1B (two-shot) | E-E-E | +10 | 1 | 0 | 1.000 |

## Random selection across seeds (Gemma 3 4B)

Seeds 43 and 44 change only the random demonstration pairs (generation seed stays 42). The spread shows how far random can move by chance; a strategy gap smaller than it is not evidence.

| Condition | Random seed 42 | Random seed 43 | Random seed 44 | Random range | Similarity |
|---|---|---|---|---|---|
| U-U-U | 6/10 | 6/10 | 9/10 | 6–9 | 9/10 |
| U-U-E | 8/10 | 7/10 | 8/10 | 7–8 | 7/10 |
| U-E-E | 8/10 | 9/10 | 7/10 | 7–9 | 8/10 |
| E-E-E | 9/10 | 8/10 | 8/10 | 8–9 | 9/10 |
| ALL | 31/40 | 30/40 | 32/40 | 30–32 | 33/40 |

## Two examples vs zero-shot (same model)

| Model | Condition | Zero-shot | Two-shot random | Two-shot similarity |
|---|---|---|---|---|
| Gemma 3 4B | U-U-U | 8/10 | 6/10 | 9/10 |
| Gemma 3 4B | U-U-E | 7/10 | 8/10 | 7/10 |
| Gemma 3 4B | U-E-E | 7/10 (U-U-E) | 8/10 | 8/10 |
| Gemma 3 4B | E-E-E | 8/10 | 9/10 | 9/10 |
| Gemma 3 1B | U-U-U | 1/10 | 0/10 | 0/10 |
| Gemma 3 1B | U-U-E | 2/10 | 1/10 | 2/10 |
| Gemma 3 1B | U-E-E | 2/10 (U-U-E) | 2/10 | 2/10 |
| Gemma 3 1B | E-E-E | 4/10 | 4/10 | 5/10 |

## Reasoning errors vs format failures (all strategies pooled per arm and condition)

Wrong answer = a parsed but wrong number. Format failures = cut off at the 2048-token limit, no marker, or ambiguous marker. Answer only = under 40 output tokens. Off-language = solution mainly in the other script than the target question. Lenient = independent cross-check (number after the last literal FINAL_ANSWER, colon optional); since parser version 2 it should equal Correct. See `scripts/error_breakdown.py`.

| Arm | Condition | n | Correct | Lenient | Wrong answer | Cut off | No/ambiguous marker | Answer only | Off-language |
|---|---|---|---|---|---|---|---|---|---|
| Gemma 4 31B (two-shot) | U-U-U | 20 | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| Gemma 4 31B (two-shot) | U-U-E | 20 | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| Gemma 4 31B (two-shot) | U-E-E | 20 | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| Gemma 4 31B (two-shot) | E-E-E | 20 | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| Gemma 3 4B (two-shot) | U-U-U | 20 | 15 | 15 | 5 | 0 | 0 | 0 | 0 |
| Gemma 3 4B (two-shot) | U-U-E | 20 | 15 | 15 | 4 | 1 | 0 | 0 | 0 |
| Gemma 3 4B (two-shot) | U-E-E | 20 | 16 | 16 | 4 | 0 | 0 | 0 | 8 |
| Gemma 3 4B (two-shot) | E-E-E | 20 | 18 | 18 | 2 | 0 | 0 | 0 | 0 |
| Gemma 3 4B zero-shot | U-U-U | 10 | 8 | 8 | 2 | 0 | 0 | 0 | 0 |
| Gemma 3 4B zero-shot | U-U-E | 10 | 7 | 7 | 2 | 0 | 1 | 0 | 1 |
| Gemma 3 4B zero-shot | E-E-E | 10 | 8 | 8 | 2 | 0 | 0 | 0 | 0 |
| Gemma 3 1B (two-shot) | U-U-U | 20 | 0 | 0 | 19 | 1 | 0 | 12 | 0 |
| Gemma 3 1B (two-shot) | U-U-E | 20 | 3 | 3 | 11 | 5 | 1 | 0 | 15 |
| Gemma 3 1B (two-shot) | U-E-E | 20 | 4 | 4 | 10 | 6 | 0 | 0 | 16 |
| Gemma 3 1B (two-shot) | E-E-E | 20 | 9 | 9 | 9 | 2 | 0 | 1 | 0 |
| Gemma 3 1B zero-shot | U-U-U | 10 | 1 | 1 | 3 | 6 | 0 | 1 | 9 |
| Gemma 3 1B zero-shot | U-U-E | 10 | 2 | 2 | 3 | 4 | 1 | 0 | 10 |
| Gemma 3 1B zero-shot | E-E-E | 10 | 4 | 4 | 6 | 0 | 0 | 0 | 0 |

## Parser change (version 2, pending approval): scores before and after

Same raw responses, re-scored. Version 2 reads the number after the last FINAL_ANSWER that has one (colon optional) and falls back to the earlier rule only when there is none. See `docs/parser_change_2026-11-25.md`.

| Run | Correct before | Correct after | Gained | Lost | Parse failures before | after |
|---|---|---|---|---|---|---|
| Gemma 4 31B (two-shot) | 80/80 | 80/80 | 0 | 0 | 0 | 0 |
| Gemma 3 4B (two-shot) | 61/80 | 64/80 | 3 | 0 | 7 | 1 |
| Gemma 3 4B zero-shot | 14/30 | 23/30 | 9 | 0 | 13 | 1 |
| Gemma 3 1B (two-shot) | 16/80 | 16/80 | 0 | 0 | 15 | 15 |
| Gemma 3 1B zero-shot | 7/30 | 7/30 | 0 | 0 | 11 | 11 |
| Gemma 3 4B random, seed 43 | 29/40 | 30/40 | 1 | 0 | 1 | 0 |
| Gemma 3 4B random, seed 44 | 30/40 | 32/40 | 2 | 0 | 3 | 0 |

## Caveats

- 10 questions per cell: one question is 10 points. An exact McNemar test reaches p < 0.05 only if at least 6 questions differ and all go the same way (6–0 gives p = 0.031; 5–0 gives 0.063; 6–1 gives 0.125).
- All questions are GSM8K training items, so memorisation cannot be ruled out, most of all for the 31B model.
- 4B and 1B are 4-bit (Q4_K_M) local builds; 31B is the hosted full model. Size is not the only difference.
- One selection seed (42), except the 4B random seed check (42, 43, 44). The deferred diversity/complexity selectors, 4-shot prompts and MGSM are not included.
