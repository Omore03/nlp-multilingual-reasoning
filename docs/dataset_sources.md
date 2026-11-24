# Dataset provenance, schema, and usage notes

Checked 2026-11-09 (Asia/Karachi). The PDF proposal is background context; its dataset plan is not an instruction to substitute MGSM evaluation records for GSM8K training records.

| Dataset | Pinned source/version | Splits and exact fields | License and usage |
|---|---|---|---|
| Original GSM8K | OpenAI [grade-school-math](https://github.com/openai/grade-school-math) commit `3101c7d5072418e28b9008a6636bde82a006892c`; `grade_school_math/data/train.jsonl` blob SHA `7d97154b91aef28d01c3301741c81ce90039a4b1`. Hugging Face `openai/gsm8k`, `main` config, was used as the accessible row viewer. | Raw `train.jsonl` and `test.jsonl`: one JSON object per line with **`question`** and **`answer`** strings; no source ID. Final numeric key is after `####` in `answer`. 7,473 train; 1,319 test. | [OpenAI repository MIT license](https://github.com/openai/grade-school-math/blob/master/LICENSE). Preserve notice on redistribution. This package selects only training questions. |
| Original English MGSM | Google Research [url-nlp/mgsm](https://github.com/google-research/url-nlp/tree/main/mgsm) commit `452a21ad3dae5668c06ceeac21ff073e1e40f9be`. `mgsm_en.tsv` is the source test file; `exemplars.py` holds eight few-shot examples. The inspected Hugging Face wrapper snapshot is `juletxara/mgsm` commit `8baeab29daaaf28d85cce812d71b5bc5e4c45c90`. | `mgsm_en.tsv`: 250 headerless TSV rows, column 1 English question, column 2 numeric answer. **There are no field names in the TSV.** The `juletxara/mgsm` Hugging Face wrapper uses `en` config; `train` 8 and `test` 250; wrapper fields **`question`**, **`answer`**, **`answer_number`**, **`equation_solution`**. In test, `answer` and `equation_solution` are null. | The original [MGSM directory license](https://github.com/google-research/url-nlp/blob/main/mgsm/LICENSE) is **CC BY 4.0**; retain attribution and change notice. The Hugging Face wrapper displays **CC BY-SA 4.0**, which conflicts with the original directory license. Cite the original source and verify downstream terms before redistribution of the wrapper. MGSM is evaluation material; do not tune on its 250 test questions. |
| Traversaal Urdu MGSM | The proposal's `large-traversaal/mgsm_urdu_cleaned` URL was inaccessible (401). The accessible [repository](https://huggingface.co/datasets/large-traversaal/mgsm_urdu_final) is **`large-traversaal/mgsm_urdu_final`**; its card calls the dataset `mgsm_urdu_cleaned`. Pinned card commit `c5aa51bcdb70a38d5784753d4a33a8895118b25d`. | Parquet `train` 8, `test` 250. The actual viewer/metadata fields are **`question`**, **`urdu_question`**, **`answer`**, **`urdu_answer`**, **`answer_number`** (int64), **`equation_solution`**. The prose table instead spells **`urd_question`** and **`urd_answer`**; use the actual Parquet schema and inspect it on load. | The [card](https://huggingface.co/datasets/large-traversaal/mgsm_urdu_final/blob/main/README.md) asks users to cite UrduBench and describes evaluation and possible fine-tuning. It has **no explicit license declaration** visible in the repository/card, so do not infer one. The 250 test items are reserved for evaluation; no rows from this dataset appear in this package. |

## Selection and checks

- The 20 demonstration and 10 development items are different GSM8K `train` questions. All 30 English questions were matched exactly against the [OpenAI GSM8K train viewer](https://huggingface.co/datasets/openai/gsm8k/viewer/main/train?p=0); 23 complete source answer keys were visible and matched. The pinned original repository is the intended immutable reference for the remaining byte-level check.
- Synthetic IDs use the first 12 hexadecimal digits of SHA-256 over the stored English question. The validator catches duplicate IDs and demo/dev overlap. Full raw-source question/answer comparison remains an optional command until the source file is supplied locally.
- Numeric arithmetic uses Python `Decimal` and a restricted expression parser. Every final step must equal `answer_number`; English and Urdu solutions must end with the same `####` number. Digit sets in paired questions must match. These checks do **not** prove a natural-language translation preserves every quantifier or unit.
- Exact-question MGSM leakage can be checked with the optional `--mgsm-en` input. The source split distinction provides the primary separation: this package uses GSM8K train, whereas the [MGSM paper](https://openreview.net/pdf?id=fR3wGCk-IXp) says its 250 evaluation questions are the first 250 GSM8K test examples. Keep evaluation questions out of all selection and tuning workflows.
- Source ambiguities are attached to individual records and listed in `review_queue.csv`, including the original GBP/USD solution inconsistency and the Friday-average wording.

## References

- [OpenAI GSM8K repository and file format](https://github.com/openai/grade-school-math)
- [OpenAI GSM8K MIT license](https://github.com/openai/grade-school-math/blob/master/LICENSE)
- [Original Google MGSM files and description](https://github.com/google-research/url-nlp/tree/main/mgsm)
- [Original Google MGSM CC BY 4.0 license](https://github.com/google-research/url-nlp/blob/main/mgsm/LICENSE)
- [Hugging Face MGSM wrapper schema and license label](https://huggingface.co/datasets/juletxara/mgsm)
- [Traversaal Urdu repository and card](https://huggingface.co/datasets/large-traversaal/mgsm_urdu_final)

## Integration source check: 25 November 2026

The pinned original training file was downloaded and checked locally. All 30 English questions and numeric keys match: 25 questions exactly, five after collapsing whitespace. See `data/review/source_verification.json` for the source hash and per-item results. Reproduce with `python scripts/verify_gsm8k_source.py --train /path/to/train.jsonl`. This supersedes the optional-source-check status above; it does not independently verify Urdu translations or full solution text.
