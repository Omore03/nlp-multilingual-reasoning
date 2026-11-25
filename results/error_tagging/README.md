# Error-tagging worksheet

`error_tagging_sheet.csv` (UTF-8, opens in Excel/Sheets) has 32 rows: all 16 non-correct two-shot answers from
Gemma 3 4B, plus a fixed sample of 16 from Gemma 3 1B (the first 2 by question ID in each strategy/condition cell).
No tags are filled in; they need a human reading of the `response` column.

Columns to use: `question_ops` (operations in the reviewed solution of the question), `demo1_ops` / `demo2_ops` (the two
solved examples shown), `auto_category` (from `scripts/error_breakdown.py`), `response` (the model's full answer).

Fill `tag_primary` (and optionally `tag_secondary`) with one of:

- arithmetic slip
- wrong plan / misread question
- copied the operation from an example
- language or translation issue
- format only (right number, unparsed)
- repetition loop / cut off
- other

"copied the operation from an example" fits when the response follows an example's operation sequence where the question
needs a different one (compare `question_ops` with `demo1_ops` / `demo2_ops`). Operations come from Hussain's reviewed
`data/review/calculations.json`, are for analysis only, and are never used for selection or prompting.
Regenerate with `python scripts/error_tagging_sheet.py`.
