# Baseline paired comparisons

Exploratory unadjusted exact two-sided McNemar tests. Ten paired questions per cell; no independent-observation pooling across conditions or strategies. Wilson intervals are per cell, not across repeated configurations.

| Comparison | Model | Condition | Difference (pp) | First only | Second only | p |
|---|---|---|---|---|---|---|
| similarity vs random seed42 | 31b | U-U-U | +0 | 0 | 0 | 1.000 |
| similarity vs random seed42 | 31b | U-U-E | +0 | 0 | 0 | 1.000 |
| similarity vs random seed42 | 31b | U-E-E | +0 | 0 | 0 | 1.000 |
| similarity vs random seed42 | 31b | E-E-E | +0 | 0 | 0 | 1.000 |
| similarity vs random seed42 | 4b | U-U-U | +30 | 3 | 0 | 0.250 |
| similarity vs random seed42 | 4b | U-U-E | -10 | 0 | 1 | 1.000 |
| similarity vs random seed42 | 4b | U-E-E | +0 | 0 | 0 | 1.000 |
| similarity vs random seed42 | 4b | E-E-E | +0 | 0 | 0 | 1.000 |
| two-shot random vs zero-shot | 4b | U-U-U | -20 | 1 | 3 | 0.625 |
| two-shot similarity vs zero-shot | 4b | U-U-U | +10 | 1 | 0 | 1.000 |
| two-shot random vs zero-shot | 4b | U-U-E | +10 | 1 | 0 | 1.000 |
| two-shot similarity vs zero-shot | 4b | U-U-E | +0 | 1 | 1 | 1.000 |
| two-shot random vs zero-shot | 4b | U-E-E | +10 | 1 | 0 | 1.000 |
| two-shot similarity vs zero-shot | 4b | U-E-E | +10 | 1 | 0 | 1.000 |
| two-shot random vs zero-shot | 4b | E-E-E | +10 | 1 | 0 | 1.000 |
| two-shot similarity vs zero-shot | 4b | E-E-E | +10 | 1 | 0 | 1.000 |
| similarity vs random seed42 | 1b | U-U-U | +0 | 0 | 0 | 1.000 |
| similarity vs random seed42 | 1b | U-U-E | +10 | 1 | 0 | 1.000 |
| similarity vs random seed42 | 1b | U-E-E | +0 | 1 | 1 | 1.000 |
| similarity vs random seed42 | 1b | E-E-E | +10 | 1 | 0 | 1.000 |
| two-shot random vs zero-shot | 1b | U-U-U | -10 | 0 | 1 | 1.000 |
| two-shot similarity vs zero-shot | 1b | U-U-U | -10 | 0 | 1 | 1.000 |
| two-shot random vs zero-shot | 1b | U-U-E | -10 | 1 | 2 | 1.000 |
| two-shot similarity vs zero-shot | 1b | U-U-E | +0 | 1 | 1 | 1.000 |
| two-shot random vs zero-shot | 1b | U-E-E | +0 | 1 | 1 | 1.000 |
| two-shot similarity vs zero-shot | 1b | U-E-E | +0 | 2 | 2 | 1.000 |
| two-shot random vs zero-shot | 1b | E-E-E | +0 | 0 | 0 | 1.000 |
| two-shot similarity vs zero-shot | 1b | E-E-E | +10 | 1 | 0 | 1.000 |

## Per-cell uncertainty

| Model | Method | Condition | Correct/n | Wilson 95% interval |
|---|---|---|---|---|
| 31b | random | U-U-U | 10/10 | 72.2% to 100.0% |
| 31b | similarity | U-U-U | 10/10 | 72.2% to 100.0% |
| 31b | random | U-U-E | 10/10 | 72.2% to 100.0% |
| 31b | similarity | U-U-E | 10/10 | 72.2% to 100.0% |
| 31b | random | U-E-E | 10/10 | 72.2% to 100.0% |
| 31b | similarity | U-E-E | 10/10 | 72.2% to 100.0% |
| 31b | random | E-E-E | 10/10 | 72.2% to 100.0% |
| 31b | similarity | E-E-E | 10/10 | 72.2% to 100.0% |
| 4b | random | U-U-U | 6/10 | 31.3% to 83.2% |
| 4b | similarity | U-U-U | 9/10 | 59.6% to 98.2% |
| 4b | random | U-U-E | 8/10 | 49.0% to 94.3% |
| 4b | similarity | U-U-E | 7/10 | 39.7% to 89.2% |
| 4b | random | U-E-E | 8/10 | 49.0% to 94.3% |
| 4b | similarity | U-E-E | 8/10 | 49.0% to 94.3% |
| 4b | random | E-E-E | 9/10 | 59.6% to 98.2% |
| 4b | similarity | E-E-E | 9/10 | 59.6% to 98.2% |
| 1b | random | U-U-U | 0/10 | 0.0% to 27.8% |
| 1b | similarity | U-U-U | 0/10 | 0.0% to 27.8% |
| 1b | random | U-U-E | 1/10 | 1.8% to 40.4% |
| 1b | similarity | U-U-E | 2/10 | 5.7% to 51.0% |
| 1b | random | U-E-E | 2/10 | 5.7% to 51.0% |
| 1b | similarity | U-E-E | 2/10 | 5.7% to 51.0% |
| 1b | random | E-E-E | 4/10 | 16.8% to 68.7% |
| 1b | similarity | E-E-E | 5/10 | 23.7% to 76.3% |
