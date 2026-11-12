# Run guide

Complete the [README setup](../README.md#quick-start) first. All paths and commands are relative to the repository root.

## Offline checks

The README commands run tests, preview, mock smoke and the full mock matrix without a key. Use `results/mock/local-*.jsonl` for local runs; these outputs are ignored. Committed examples preserve earlier runs and may reject resume on another environment.

## Live synthetic smoke

After configuring the free API settings:

```bash
python -m src.inference.runner preview --config configs/live_smoke.yaml --question-limit 1
python -m src.inference.runner run --config configs/live_smoke.yaml --question-limit 1 --resume
```

This config covers one synthetic question and all four conditions. The existing verified journal may resume with zero calls if its fingerprints match. For a fresh smoke on a different environment, use a fresh output path:

```bash
python -m src.inference.runner run --config configs/live_smoke.yaml --question-limit 1 --output results/live_smoke/local-smoke.jsonl --resume
```

Four successful conditions create an adjacent `model_verification.json`. Review the visible solutions, Urdu text, truncation and `FINAL_ANSWER:` formatting. If adopting a new receipt, update `verification_receipt` in the pilot config. A change to model settings requires a new smoke and receipt.

## Integrate and run the real pilot

The real pilot is currently blocked. Follow the [handoff status](handoff_status.md) and [integration contract](integration_contract.md) before using these commands:

1. Add Hussain's reviewed data to `data/processed/demo_pool.jsonl` and `data/processed/dev.jsonl`, with his validator and provenance.
2. Add Rayyan's actual selectors, tests and pinned dependencies. Configure `selector` and `selector_version` in `configs/pilot.yaml`. Preserve Urdu retrieval; use a thin adapter if needed.
3. Run both members' checks and the project tests. Review the selected IDs and rendered prompts. Keep the verified model settings fixed.

```bash
python -m pytest -q
python -m src.inference.runner preview --config configs/pilot.yaml --question-limit 1
python -m src.inference.runner run --config configs/pilot.yaml --question-limit 1 --resume
# Extend the same plan when free quota permits.
python -m src.inference.runner run --config configs/pilot.yaml --question-limit 5 --resume
python -m src.inference.runner run --config configs/pilot.yaml --resume
```

The one-question run expects eight successes. Extending to five questions expects 40 total; the full plan expects 80. Retries consume additional quota. `--question-limit` uses the first N dev records without changing experiment identity. Never substitute draft or synthetic data into production paths.

## Outputs and resume

Each run writes a JSONL journal and adjacent `.manifest.json` with configuration, data/source/software fingerprints and the full prompt plan. Each row is flushed and synced. Failure attempts remain in the journal; count unique successful record IDs, not lines.

Resume checks the frozen plan and fingerprints, skips successes and retries failures. Changed data, source, selection or software require a new output. Preserve the earlier files; freeze the checkout between real pilot segments. One writer can hold the output lock.

An interrupted remote call can use quota without leaving a saved response. Retrying that record may make another request.

## Damaged output

An unfinished final JSONL line stops resume. Inspect the file before explicitly repairing it:

```bash
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-matrix.jsonl --resume --repair-tail
```

For the real pilot, use `--config configs/pilot.yaml` without the mock output override. Repair backs up the entire journal to `.corrupt-<timestamp>`. It completes the newline for valid final JSON, or removes only an invalid unfinished tail. Interior corruption, duplicate successes and identity conflicts still stop the run. Keep backups locally.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Requested scope finished, including a no-op resume |
| 1 | This invocation wrote terminal failures |
| 2 | Configuration, integration, access or journal error |
| 3 | Local request budget deferred unfinished work |

A successful limited smoke does not mean the full pilot is complete. Read the output summary and inspect failures before resuming. Wait for free quota; never upgrade billing or switch to a paid fallback.
