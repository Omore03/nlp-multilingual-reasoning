# Integration contract

Hussain owns data validation and review, Rayyan owns selection, Ammar owns prompting/inference, and Saad owns evaluation. The [handoff status](handoff_status.md) records current integration gaps.

## Real input files

`data/processed/demo_pool.jsonl` must contain 20 reviewed bilingual demonstrations. Each UTF-8 JSONL row has:

```json
{"id":"demo-001","question_en":"...","question_ur":"...","reasoning_en":"full worked solution","reasoning_ur":"مکمل حل","answer":"1200","verified":true}
```

`data/processed/dev.jsonl` must contain 10 separate, reviewed GSM8K training questions:

```json
{"id":"dev-001","question_en":"...","question_ur":"...","answer":"1200"}
```

These examples illustrate fields only. IDs must be unique and disjoint across files. Answers are plain numeric strings: no units, commas or exponent notation. The accepted pattern is `-?(0|[1-9][0-9]*)(\.[0-9]+)?`.

Demo reasoning must include complete operations and units. The template appends the final-answer marker, so reasoning should not duplicate `FINAL_ANSWER:`. Real demos require boolean `verified: true` based on actual review. Dev accepts an optional boolean `verified`; its absence does not establish review. Keep reviewer evidence and uncertainties in the dataset notes.

The loader checks structure, counts and IDs. Hussain's validator and human review establish source membership, arithmetic and translation quality. Do not use MGSM evaluation data in this pilot.

Hussain's supplied generator uses different names: map `solution_en`/`solution_ur` to `reasoning_en`/`reasoning_ur`, and `answer_number` to numeric-string `answer`. Preserve provenance and derive verification only from confirmed review. This adapter is still pending.

## Selector interface

```python
select_examples(query, pool, k, strategy, seed) -> list[str]
```

| Argument | Contract |
| --- | --- |
| `query` | Exactly `{"id": "...", "question_ur": "..."}`; no dev answer or English text |
| `pool` | A copied list of bilingual demonstration records |
| `k` | 2 |
| `strategy` | `random` or `similarity` |
| `seed` | Configured unsigned integer, initially 42 |
| Return | Two unique existing demo IDs in intended prompt order |

Use Urdu retrieval for every condition, including E-E-E. The runner selects once per question/strategy and reuses the same ordered IDs across conditions.

Configure the real callable in `configs/pilot.yaml`; the reserved default is `src.selection.select:select_examples`. Use a thin adapter if needed, without exposing dev answers. Set `selector_version` to identify the code, encoder revision, cache identity and seed policy. Pin dependencies. Document any stable per-query seed derivation; never use Python's randomized `hash()`.

The manifest hashes the source and checks the full selection plan on resume. Changing external encoder/cache identity requires a version update. `tests/fixtures/selector.py` is only a fixed test table, and production mode rejects it.

## Prompt convention

Template version: `bilingual-math-2shot-v1`. Condition letters mean target question / demonstrations / instructions. U means Urdu; E means English. Exactly two solved demonstrations precede one target question. The requested solution follows the target language; labels follow instruction language. Target gold is excluded.

All conditions use the same final line:

```text
FINAL_ANSWER: 1200
```

A successful API call does not establish answer correctness or format compliance. Saad owns parsing and grading.

## Raw outputs for Saad

The real journal is `results/pilot_raw.jsonl`. Keep its adjacent manifest and all attempt history. Reconcile **80 unique successful record IDs**: 10 questions × 2 strategies × 4 conditions.

| Group | Fields |
| --- | --- |
| Experiment | `question_id`, `condition`, `strategy`, `shot_count`, `seed`, ordered `demo_ids` |
| Content | `prompt`, `raw_response`, `prompt_hash` |
| Identity | `run_id`, `record_id`, `configuration_hash`, `data_fingerprints`, `template_version` |
| Model | `backend`, `provider`, `model_id`, `inference_settings`, `served_model`, `served_provider` |
| Execution | `status`, UTC `timestamp`, `attempts`, `latency_seconds`, `mode`, `data_kind` |
| Provider metadata | Available `request_id`, `usage`, `finish_reason`, `model_access_metadata` |

The native Google path also records `free_project_tier_confirmed_by_user`. This is user confirmation, not a billing audit. Token usage is retained; measured dollar cost is omitted when unavailable. Visible text excludes separate thought parts.

Failures retain the experiment identity, prompt and sanitized error details, with no fabricated response. Filter `status == "success"` and deduplicate by record ID before evaluation. A failed attempt followed by success counts once.

Saad joins dev gold by question ID and writes `prediction`, `gold_answer`, `correct` and `parse_status` into a separate evaluated artifact. Leave raw journals unchanged. Never include synthetic or mock records in research metrics.

## Acceptance

Before the real pilot: reviewed 20/10 data, disjoint IDs, two tested real selectors, reviewed prompts and a matching four-condition live model receipt. Then run the [pilot commands](running.md). Completion needs 80 real successes or an explicit account of unresolved failures. Evaluation and final submission remain separate requirements.
