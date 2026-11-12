# Integration contract

## Ownership and production inputs

Hussain owns acquisition, translations, dataset provenance, complete validation and human review. Ammar's loader performs only structural boundary checks. Rayyan owns both production selectors and embedding dependencies/caches. Saad owns parsing, grading, statistics and reports. No pending teammate module is recreated here.

`data/processed/demo_pool.jsonl`: exactly 20 UTF-8 JSON objects, one per line:

```json
{"id":"gsm8k-train-demo-001","question_en":"...","question_ur":"...","reasoning_en":"complete worked solution","reasoning_ur":"مکمل حل","answer":"1200","verified":true}
```

This is a schema illustration, not supplied data. `verified` must be boolean true for real demos and must reflect actual human review. Both reasoning fields must contain full solutions, including operations and units. The template appends a consistent final answer line; Hussain should avoid duplicating the literal final marker within reasoning text.

`data/processed/dev.jsonl`: exactly 10 distinct training development questions:

```json
{"id":"gsm8k-train-dev-001","question_en":"...","question_ur":"...","answer":"1200"}
```

Development translations must be reviewed, but the agreed schema does not require `verified`. An optional boolean `verified` is accepted; its absence is not a claim of verification. Human review evidence belongs in Hussain's dataset notes. Do not automatically insert true. IDs are strings and unique within files, with no overlap between pool/dev. Answers are strings matching `-?(0|[1-9][0-9]*)(\.[0-9]+)?`, without commas, units or exponent notation. This is input checking, not Saad's response normalization/parser.

The loader rejects missing fields, wrong primitive types, duplicate/overlapping IDs and wrong counts. Mathematical equivalence, source split, translation accuracy and review evidence remain Hussain's checks. Do not use MGSM for this initial pilot.

## Selector boundary

```python
select_examples(query, pool, k, strategy, seed) -> list[str]
```

- `query` is exactly `{"id": <development ID>, "question_ur": <Urdu question string>}`. No English question, development answer or evaluation metadata is sent.
- `pool` is a copied list of bilingual demonstration dictionaries; demo answers/reasoning are legitimate solved examples.
- `k` is exactly 2. `strategy` is `random` or `similarity`. `seed` is the configured unsigned integer, initially 42.
- Return exactly two unique existing demo IDs in intended prompt order. The runner validates membership/uniqueness and preserves that order.

Retrieval always uses Urdu, including E-E-E. Rendering language never changes retrieval language. Select once per query/strategy before the four-condition loop. Selection receives the same seed across queries, with stable input order; the query ID is available to Rayyan if his implementation uses a documented per-query derivation. No built-in Python `hash()` is used. If an adapter derives a seed, use SHA-256 of a documented canonical `(base_seed, query_id, strategy, k)` representation and version that policy. No such derivation is necessary in this runner.

The configured callable defaults to `src.selection.select:select_examples`. If Rayyan expects a bare Urdu string, a small wrapper can pass `query['question_ur']` to his function. If he expects another dictionary schema, adapt only those fields. Preserve Urdu retrieval and never copy development gold into the adapter. Set `selector_version` to include his code/encoder revision and relevant cache identity, and pin his dependencies. The manifest also hashes Python files under the selector's directory and all `src/` files; an external encoder or cache revision must be represented explicitly by `selector_version`.

Do not change pool order or seed policy mid-run. On resume selection is recomputed and checked against the frozen full plan; a nondeterministic selector is rejected as incompatible. `tests/fixtures/selector.py` returns fixed ID pairs and is only test infrastructure. Production mode rejects selectors from `tests.*` and cannot use a mock backend.

## Prompt convention

Template version: `bilingual-math-2shot-v1`, centralized in `src/prompting/templates.py`. Conditions list question/demo/instruction languages respectively: U-U-U, U-U-E, U-E-E, E-E-E. Exactly two complete demonstrations are followed by one target. Labels follow instruction language. Solutions are requested in the target question language. Target gold is never read by template construction.

Across every language condition the final terminal line uses the literal ASCII marker and a numerical value:

```text
FINAL_ANSWER: 1200
```

Urdu instructions explain that same literal marker naturally in Urdu. Demonstrations also show it. Saad should parse the response's final numerical answer according to this convention, with his own documented ambiguity and numeral policies. The runner does not parse or grade it. A request succeeding does not establish marker adherence or accuracy.

## Raw output contract for Saad

`results/pilot_raw.jsonl` contains success and failure attempts. Filter `status == "success"`; reconcile **80 distinct record IDs** across 10 questions × 2 strategies × 4 conditions. A failure later followed by success is retained; never count journal lines as completed experiments.

Success fields: `question_id`, `condition`, `strategy`, `shot_count`, `seed`, `model_id`, ordered `demo_ids`, full `prompt`, `raw_response`. Additional provenance: `run_id`, `record_id`, `backend`, route `provider`, actual requested `inference_settings`, `template_version`, `configuration_hash`, dataset SHA-256 `data_fingerprints`, UTC `timestamp`, `mode` (mock/live), `data_kind`, `request_id`, numeric `usage`, `served_model`, `served_provider`, `finish_reason`, `attempts`, `latency_seconds`, `prompt_hash`.

Failure records retain the same experiment identity and prompt with `status: failure`, sanitized error code/transient flag, attempts and latency; no fake response is written. Bad credentials/parameters stop global execution after recording the failure. Retry budgets are documented in model_decision.md. No key, authorization header or provider error-body text is persisted. A locally absent key is reported before calls.

Saad later adds `prediction`, `gold_answer`, `correct`, `parse_status` in a separate evaluated artifact. Join gold from Hussain's dev data by ID, preserve raw files/manifests and do not edit raw inference journals in place. No such evaluation fields, metrics or research report are implemented by Ammar.

## Commands and real acceptance

```bash
# Preflight without model calls, after integrating real data/selectors:
python -m src.inference.runner preview --config configs/pilot.yaml --question-limit 1
# Four-condition live synthetic access verification:
python -m src.inference.runner run --config configs/live_smoke.yaml --question-limit 1 --resume
# Real one-question smoke (both selectors, eight records), then complete/resume:
python -m src.inference.runner run --config configs/pilot.yaml --question-limit 1 --resume
python -m src.inference.runner run --config configs/pilot.yaml --resume
```

Actual integration requires Hussain's 20 checked demos and 10 separate reviewed dev questions plus validator/notes; Rayyan's two tested selectors, dependencies and retrieval review; matching live model verification receipt; and exactly 80 successful experiment combinations or an explicit failure inventory. Saad's scoring/reconciliation/report is a separate team completion requirement. These remain pending. The fixture 80-record matrix proves engineering coverage only.
