# Output separation

`mock/` contains deterministic synthetic engineering evidence only. `live_smoke/` is reserved for authenticated model calls on synthetic questions and is ignored initially. `pilot_raw.jsonl` and `pilot_raw.manifest.json` are reserved for the actual integrated pilot, pending real data, selectors and verified access. No actual pilot has been run. Live/pilot outputs require explicit provenance/secret review before selective Git tracking. Saad owns evaluated outputs and research reporting.

Current live verification path is `live_smoke/gemma_free_smoke.jsonl` for the fixed free Gemma model. The earlier blocked paid-model preflight manifest is historical, contains no inference response and cannot authorize the current pilot. No live result is claimed.
