# Run and recovery guide

Follow the README setup. Use Python 3.12 and run commands from the repository root.

## Check inputs and prompts

```bash
python -m src.data.validate
python -m pytest -q
python -m src.inference.runner preview --config configs/pilot.yaml --question-limit 1
```

The current real plan is fixed at 18 approved demos, 10 dev questions, two shots, two strategies and four conditions. Review selected IDs and language rendering before calls. The adapter uses genuine frozen selections and does not load model weights.

## Collect the real pilot

Configure the existing unbilled free Google project in ignored `.env`; see [model setup](model_decision.md).

```bash
python -m src.inference.runner run --config configs/pilot.yaml --question-limit 1 --resume
python -m src.inference.runner run --config configs/pilot.yaml --resume
```

The limited run covers eight records, included in the full 80-record plan. Failures are retained and retried on resume. Each invocation permits at most 40 generation attempts, including retries. Wait when project quota or provider capacity is unavailable; never upgrade billing or switch to a paid fallback.

Keep source, dependencies, data, frozen selections and settings unchanged between segments. Every journal has an adjacent `.manifest.json`. Resume validates the complete prompt plan and fingerprints before skipping successes. One writer can hold the output lock.

## Score a real run

```bash
python -m src.evaluation.report --raw results/pilot_raw.jsonl --dev data/processed/dev.jsonl --manifest results/pilot_raw.manifest.json --out-dir results
```

The evaluator verifies the real manifest, input hash and each record's identity, settings, selected IDs and prompt. It writes evaluated JSONL, CSV/Markdown summaries and reconciliation separately from raw responses. Inspect `complete`, expected/scored counts and parse failures before using results. Partial output is not a completed baseline.

For Saad's explicit synthetic fixtures only:

```bash
python -m src.evaluation.report --raw tests/fixtures/eval_raw_responses.jsonl --dev tests/fixtures/eval_dev.jsonl --out-dir results/mock/local-evaluation --prefix fixture --allow-fixtures
```

That fixture is intentionally incomplete, so exit 1 is expected. Fixture outputs are labelled non-research.

## Reproduce selections

The tracked frozen plan is enough to preview and run this exact pilot on a clean clone. To independently regenerate it, use the tracked original cache:

```bash
python scripts/freeze_selection.py --cache data/selection/vectors/sentence-transformers_paraphrase-multilingual-mpnet-base-v2_4328cf26390c98c5e3c738b4460a05b95f4911f5.npz
```

The script verifies the audited cache hash, uses Rayyan's real selectors and refuses missing vectors. Edited or new questions require genuine new embeddings and a separately reviewed experiment; never substitute the test encoder.

## Damaged output

Resume stops on an unfinished final line. Inspect the journal before using `--resume --repair-tail`. Repair first backs up the complete file to `.corrupt-<timestamp>`, then finishes a valid final newline or removes only an invalid unfinished tail. Interior corruption, identity conflicts and duplicate successes still stop execution. Keep backups locally.

Exit codes: 0 means requested scope finished; 1 means terminal failures were written; 2 means invalid inputs/access/journal; 3 means the local attempt budget deferred work. A limited smoke returning 0 does not imply all 80 records are complete.
