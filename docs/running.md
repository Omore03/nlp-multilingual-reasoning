# Run and recovery guide

For the current baseline, follow [reproduction instructions](../REPRODUCE_BASELINE.md). They cover the seven inherited runs, scoring into separate folders, all config previews, mock resume, optional live smoke and report build.

Archived inference journals are complete and immutable. The new source fingerprint intentionally differs; do not resume an old journal with changed source, software, data, selections or settings. Rescore saved outputs offline. A new inference run requires a new allowed output such as `results/gemma3_4b_repro/pilot_raw.jsonl`.

The partial Google zero-shot reference remains 0/30 successful responses after repeated HTTP503 failures. It is separate from completed baselines. Do not switch to a paid fallback or retry capacity failures in a loop.

## Interrupted output

Resume refuses an unfinished final JSONL line. Inspect before using `--resume --repair-tail`. Repair first backs up the full file to `.corrupt-<timestamp>`, then restores a newline for a complete record or removes only an invalid unfinished tail. Interior corruption, conflicting identity and duplicate successes still stop execution. Preserve backups.

Exit codes: 0 means requested scope finished; 1 terminal failures were recorded; 2 invalid input/access/journal; 3 invocation budget deferred work. A one-question smoke returning 0 does not imply the real matrix is complete. Evaluation exits 0 only for a complete matching run; 1 means incomplete, 2 invalid provenance. Synthetic fixture scoring requires `--allow-fixtures` and never supplies research results.
