# Results

- `pilot_raw.jsonl` and its manifest: actual API attempt history and frozen plan.
- `pilot_evaluated.jsonl`: separate predictions, gold keys, correctness and parse status.
- `pilot_summary.csv` / `.md`: strategy/condition results and margins.
- `pilot_reconciliation.json`: completeness, input hashes and research eligibility.
- `mock/`: synthetic engineering checks, never research results.
- `live_smoke/google_direct/`: historical verified API responses to synthetic questions.

Count unique successful records rather than journal lines. Failures remain in the raw history. Generated files are reviewed and selectively tracked; credentials, caches and weights remain excluded.
