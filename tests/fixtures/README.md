# Synthetic test fixtures

These simple bilingual pencil-addition examples were authored for engineering checks. They are not GSM8K data or reviewed research translations.

- 20 demo rows and 10 dev rows exercise the 80-record matrix.
- Demo verification flags are false; dev omits the optional flag.
- IDs are disjoint, but content may repeat. This is not a research split.
- `selector.py` returns fixed ID pairs, not real random or similarity selections.

Keep fixtures and mock outputs separate from production data and research metrics.
