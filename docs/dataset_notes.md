# Dataset and review notes

The pilot uses GSM8K training questions provided by Hussain, converted to the agreed schema by Rayyan. Their 30 question/answer pairs and 20 demo solutions match the supplied Word review after whitespace normalization.

## Approved split

- 18 bilingual demonstration candidates, all `verified: true`.
- 10 separate bilingual development questions; approval is recorded in the review ledger.
- Two excluded demos: Julie's pages question (`gsm8k-train-4ed90b091532`) and James's letter/pages question (`gsm8k-train-2e8fc28b2be6`). Both remain false because wording corrections were requested.

The Word form has 22 explicit approvals and six unticked entries. Hussain's confirmation reported by Ammar on 25 November approves the unticked entries. We record that confirmation without backdating it to the document's 13 November signatures. See `data/review/review_receipt.json`.

## Checks and provenance

```bash
python -m src.data.validate
```

The integration checks 30 unique, disjoint IDs across approved and excluded records, approval decisions, numeric-string answers, NFC text, question digit alignment and every supplied arithmetic step. It reuses Hussain's restricted arithmetic evaluator. Arithmetic records remain in `data/review/calculations.json`; dev solutions never cross the selector boundary.

Human review is reported evidence, not an independent language-quality certification by this validator. Source ambiguities remain relevant, including Natalia's friends/clips wording and Krystian's daily-average wording. The pinned original training file has now been checked: all 30 questions match (25 exactly, five after collapsing whitespace), and all 30 numeric keys agree. See `data/review/source_verification.json`. This comparison does not certify full worked-solution or Urdu-text identity.

GSM8K source revision: `3101c7d5072418e28b9008a6636bde82a006892c`. Preserve [the source notes](dataset_sources.md) and `data/LICENSE_GSM8K.txt`. No MGSM evaluation records were acquired or used in this pilot.
