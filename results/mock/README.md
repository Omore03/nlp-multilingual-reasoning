# Mock outputs

Current recorded examples:

| File | Contents |
| --- | --- |
| `google_direct_preview.jsonl` | Eight prompt previews |
| `google_direct_smoke.jsonl` | Four successful mock records |
| `google_direct_matrix.jsonl` | 80 unique successful mock records |

The backend is **mock**, despite the revision name in the filenames. Responses contain a fixed placeholder answer and prompt digest. They do not measure mathematical accuracy, Urdu quality or selector effectiveness.

Adjacent `.manifest.json` files preserve each run's plan and fingerprints. Earlier `matrix`, `smoke`, `preview` and `free_*` examples remain historical. Use `local-*.jsonl` for fresh local checks; source or environment changes can correctly prevent resuming a committed example. See the [run guide](../../docs/running.md).
