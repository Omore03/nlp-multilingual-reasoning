# Urdu-English mathematical reasoning

University NLP project on solved-example selection and prompt language. In-context learning, without fine-tuning.

**25 November 2026: intermediate baseline submission.** Seven saved runs, **380 scored configurations on ten distinct questions**, independently verified. **285 tests pass.** Published on `intermediate-stage`; `main` is unchanged. LMS submission has not been performed.

## Individual contributions

| Member | Contribution |
|---|---|
| **Ammar Anees** | Repository/model setup, bilingual prompts, inference/resume, team integration, provenance audit, independent rescoring and report assembly |
| **Hussain Baqar** | Bilingual GSM8K data, arithmetic validator, source/license notes and review evidence; 18 approved demos, ten dev questions, two excluded demos |
| **Rayyan Hasib** | Random/similarity selectors, pinned encoder/cache and tests; local Ollama backend, 1B/4B runs, zero-shot/seed checks, proposed parser correction and analysis |
| **Saad ur Rehman** | Original numerical parser, exact-match metrics, reconciliation, summaries, tests and evaluation plan; parser/metrics are integrated; the error-tag worksheet remains a draft |

## Results

| Model | Random, seed 42 | Similarity | Zero-shot |
|---|---|---|---|
| Gemma 4 31B, hosted | 40/40 | 40/40 | Incomplete: 0/30 responses; HTTP503 |
| Gemma 3 4B, local Q4_K_M | 31/40 | 33/40 | 23/30 |
| Gemma 3 1B, local Q4_K_M | 7/40 | 9/40 | 7/30 |

4B random selection seeds 43/44 score 30/40 and 32/40; generation seed stays 42. The 4B U-U-U similarity result is 9/10 versus random seed 42's 6/10 (paired exact p=0.25); random seed 44 also reaches 9/10. **No strategy improvement is established.** Zero-shot and two-shot have different condition counts, so compare matched cells rather than aggregate percentages. [Full comparison](docs/model_comparison.md), [paired statistics](docs/baseline/statistics.md).

The adopted parser policy recovers 15 correct answers and loses none; seven more answers become parsed wrong numbers. Bounded-marker hardening leaves all 380 bundled v2 scored rows unchanged. Raw responses and both inherited score versions are preserved. The project lead has removed additional internal approval requirements. Draft tags are not presented as completed human review.

## Fixed experiment

- 18 approved bilingual demonstration candidates; ten separate reviewed GSM8K training dev questions. Demos 4/5 remain excluded.
- Two solved examples, random or Urdu semantic similarity; four conditions: **U-U-U, U-U-E, U-E-E, E-E-E** = question/examples/instructions.
- Each main model arm: ten questions x two selectors x four conditions = 80 configurations.
- Zero-shot has three unique conditions; U-E-E duplicates U-U-E without examples and is not rerun.
- Retrieval always uses Urdu. All Urdu demonstration solutions include English unit words; U-U-U is nominal Urdu.

These are development results. Model generation, runtime, precision and model-specific options differ; the comparison cannot isolate model size. Dataset expansion, MGSM, diversity/complexity and four-shot prompting are deferred.

## Setup and offline reproduction

Use Python 3.12 on macOS/Linux, from the repository root. Rayyan collected local runs with Python 3.13.18; integration checks used 3.12.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.data.validate
python -m pytest -q
python scripts/audit_baseline.py
python scripts/compare_arms.py --out docs/model_comparison.md
python scripts/baseline_statistics.py
python scripts/build_baseline_report.py
```

The review package includes saved runs for these commands. No API key or model-weight download is needed for offline scoring. [Exact reproduction](REPRODUCE_BASELINE.md).

## Reports and evidence

- [Consolidated IEEE baseline report](reports/baseline_2026_11_25/baseline_report.pdf): current intermediate report.
- [Completion record](BASELINE_COMPLETION_REPORT.md): branch, commits, checks, discrepancies and remaining decisions.
- [Audit receipt](evidence/baseline_2026_11_25/audit.json), [source checksums](evidence/baseline_2026_11_25/source_receipt.json), [parser changes](evidence/baseline_2026_11_25/parser_changes.csv), [draft error tags](evidence/baseline_2026_11_25/error_tagging_draft.csv).
- [Original 31B report](reports/intermediate/intermediate_report.pdf) is preserved. The inherited `reports/gemma3_4b/` and `reports/gemma3_1b/` are earlier single-arm report snapshots; use the consolidated report for current review.
- [Data/review notes](docs/dataset_notes.md), [selection](docs/selection_notes.md), [model setup](docs/model_decision.md), [parser policy](docs/parser_change_2026-11-25.md), [checklist](docs/submission_checklist.md).

## Live execution

Local execution requires Ollama and pinned model digests. This integration machine has no Ollama installation: no local live smoke was repeated and no weights were downloaded. [Optional live commands](REPRODUCE_BASELINE.md).

The Google route requires private `GOOGLE_API_KEY` and the existing user-confirmed free-project setting. Never upgrade billing or use a paid fallback. The 31B zero-shot attempt stopped after repeated capacity failures; it remains optional reference work. **Do not resume archived journals after source/environment changes.** Use a fresh allowed output such as `results/gemma3_4b_repro/pilot_raw.jsonl`.

The latest fully visible TA announcement gives 24 November, 11:59 PM; a later message was partly obscured. Confirm the latest deadline, submission status and meeting time with the team. The repository does not establish submission or TA acceptance.
