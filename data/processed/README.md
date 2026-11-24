# Approved pilot data

`demo_pool.jsonl` contains 18 approved bilingual GSM8K training demonstrations. `dev.jsonl` contains 10 separate reviewed training questions. Both use the runner's agreed schema.

Demos 4 and 5 remain false and live separately under `data/review/`. Review evidence and arithmetic checks are documented in [dataset notes](../../docs/dataset_notes.md).

Run `python -m src.data.validate` from the repository root. These are real-source records, not synthetic fixtures. Preserve the GSM8K license and provenance.
