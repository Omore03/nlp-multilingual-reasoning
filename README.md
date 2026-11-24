# Multilingual mathematical reasoning

University NLP project on how demonstration selection and Urdu/English prompt language affect mathematical reasoning. We use few-shot in-context learning, with no fine-tuning.

**Status: 25 November 2026.** The reviewed dataset, real selectors and evaluator are integrated. **229 offline tests pass.** The real pilot has **38/80 successful configurations**; collection is incomplete because free-provider capacity is intermittent. See [results](results/pilot_summary.md), [verification](docs/verification.md) and the [IEEE report](reports/intermediate/intermediate_report.pdf).

The intermediate deliverable was due **23 November**. Work and results collected later are dated accurately; submission and meeting arrangements must be confirmed with the TA.

## Individual contributions

| Member | Contribution |
| --- | --- |
| **Ammar Anees** | Repository and model setup; four prompt conditions; inference, logging and resume; team integration; provenance checks and report assembly |
| **Hussain Baqar** | Bilingual GSM8K data, arithmetic validator, source/license notes and human review. 18 demos and 10 dev questions approved; two demos excluded for wording corrections |
| **Rayyan Hasib** | Random and similarity selectors, tests, pinned encoder, genuine embedding cache, selection outputs, retrieval examples and designs for later methods |
| **Saad ur Rehman** | Numerical answer parser, metrics, reconciliation, summary outputs, tests and evaluation plan. Integrated with the shared marker and stricter real-run checks |

## Experiment

- **18 approved demonstration candidates**, with two solved examples per prompt.
- **10 separate reviewed dev questions** from GSM8K training data.
- **Random and Urdu semantic similarity** selection, seed 42.
- **U-U-U, U-U-E, U-E-E, E-E-E**: target question / demonstrations / instructions.
- **80 expected successful records**: 10 questions x 2 strategies x 4 conditions.

Retrieval stays Urdu in every condition. Demos 4 and 5 remain false and are excluded. This is a small development pilot, not the final MGSM evaluation.

## Setup

Use Python 3.12 on macOS or Linux, from the repository root:

```bash
git clone https://github.com/Omore03/nlp-multilingual-reasoning.git
cd nlp-multilingual-reasoning
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The pilot uses real selections frozen from Rayyan's supplied encoder vectors. **No model-weight download is needed.** Heavy encoder dependencies are optional and are not installed by the commands above.

## Local checks

```bash
python -m src.data.validate
python -m pytest -q
python -m src.inference.runner preview --config configs/pilot.yaml --question-limit 1
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-check.jsonl --resume
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-check.jsonl --resume
```

Expected: valid 18/10 data, 229 passing tests, eight real prompt previews, 80 mock successes, then zero new records. Mock outputs are engineering checks and never enter research results. Use a new local filename after a source or environment change.

## Free API and real run

Copy `.env.example` to `.env` only if you do not already have local settings. Add your Google key and set `GOOGLE_AI_STUDIO_FREE_TIER_CONFIRMED=true` only after checking the key's project is Free tier with no billing attached. Keep credentials out of Git.

The fixed model is **gemma-4-31b-it on direct Google AI Studio REST**. No paid fallback, billing upgrade, rented compute or hosted CI is used. Free capacity may require waiting and resuming.

```bash
python -m src.inference.runner run --config configs/pilot.yaml --question-limit 1 --resume
python -m src.inference.runner run --config configs/pilot.yaml --resume
python -m src.evaluation.report --raw results/pilot_raw.jsonl --dev data/processed/dev.jsonl --manifest results/pilot_raw.manifest.json --out-dir results
```

The first command covers eight records; the full run covers 80. Each invocation permits at most 40 generation attempts, including retries. Resume when free capacity permits. Keep source, dependencies, inputs and settings fixed between segments. These commands resume the original run only in its matching environment. For a new run, add `--output results/local-pilot.jsonl` to both runner commands, then score that file with its adjacent `results/local-pilot.manifest.json`. Do not append new environments to the published journal.

## Files and documentation

| Path | Contents |
| --- | --- |
| `src/prompting/`, `src/inference/` | Templates and resumable API/mock execution |
| `src/selection/` | Rayyan's selectors and the audited frozen-plan adapter |
| `src/evaluation/` | Saad's parser, scoring and reporting |
| `data/processed/` | Approved 18-demo/10-dev data |
| `data/review/` | Review evidence, arithmetic records and two excluded demos |
| `data/selection/approved_plan.json` | Genuine frozen selections and encoder/cache fingerprints |
| `results/pilot_raw.jsonl` | Real API journal, including failure history |
| `results/pilot_evaluated.jsonl`, `pilot_summary.csv` | Separate scored outputs and summaries |
| `reports/intermediate/` | IEEE report, LaTeX source and generated result tables |

- [Run and recovery guide](docs/running.md)
- [Integration contract](docs/integration_contract.md)
- [Data and review notes](docs/dataset_notes.md)
- [Selection notes](docs/selection_notes.md)
- [Team workflow](docs/team_workflow.md)
- [Verification](docs/verification.md)
- [Submission checklist](docs/submission_checklist.md)

The repo is public as observed on 25 November; this integration does not change its visibility. Final project completion still requires the later approved experiments and report.
