# Mock engineering outputs only

`matrix.jsonl`: 80 unique successful deterministic mock records across 10 synthetic questions, two fixture strategy labels and four language conditions. `smoke.jsonl`: four mock records (one question, one fixture label, four conditions). Adjacent manifests preserve the exact plans/settings/fingerprints. `preview.jsonl` contains prompt previews, not inference results.

These responses contain a fixed placeholder answer and a prompt digest. They do not demonstrate mathematical accuracy, selector effectiveness or Urdu quality. No real research results are present. Source/software changes can make these historical runs incompatible with resumption; reproduce into a new path using the README command. Locks, recovery backups and temp files are not tracked.

Current free-only runner evidence uses `free_matrix.jsonl` (80 successes), `free_smoke.jsonl` (4 successes) and `free_preview.jsonl`. Earlier `matrix`/`smoke` files are preserved historical mock evidence; their source fingerprints intentionally differ from the updated runner. All remain mock engineering artifacts.

For the native Google adapter revision, current offline outputs are `google_direct_matrix.jsonl`, `google_direct_smoke.jsonl` and `google_direct_preview.jsonl`. All still use the deterministic mock backend, not Google model inference. Previous journals/manifests are preserved.
