# Multilingual mathematical reasoning

University NLP semester project on how demonstration selection and Urdu/English prompt language affect few-shot mathematical reasoning. We use in-context learning; no fine-tuning.

**Status · 12 November 2026:** prompting and inference are implemented, 90 offline tests pass, and a live API smoke test passed all four language conditions on synthetic questions. Teammate files have arrived for review. The real pilot and final project submission are pending.

## Team contributions

| Member | Responsibility | Current contribution |
| --- | --- | --- |
| **Ammar Anees** | Repository, model setup, prompting, inference and integration | Implemented four prompt conditions, free API access, logging, retries, resume checks, tests and documentation. Synthetic live smoke verified. Team integration pending. |
| **Hussain Baqar** | Bilingual data, validation and provenance | Shared a generator for 20 demonstrations and 10 dev questions, a validator, source notes and the GSM8K license. All translations are marked draft; human review is awaiting confirmation. |
| **Rayyan Hasib** | Random and Urdu similarity selection | Shared selector code, tests and handover reports. His later report describes a completed selection run; the updated code and generated artifacts are still needed to reproduce it here. |
| **Saad ur Rehman** | Answer parsing, evaluation and reporting | Implementation and results have not yet been supplied. |

See the [handoff status](docs/handoff_status.md) for what is ready and what is missing.

## Initial pilot

- **Data:** 20 reviewed bilingual GSM8K training demonstrations and 10 separate training dev questions.
- **Selection:** random and Urdu semantic similarity, with two demonstrations per prompt.
- **Conditions:** U-U-U, U-U-E, U-E-E and E-E-E.
- **Expected output:** 2 strategies × 4 conditions × 10 questions = **80 successful records**.

The condition letters mean **target question / demonstrations / instructions**, with U for Urdu and E for English. Retrieval uses Urdu for every condition. Final MGSM evaluation and the larger experiments are later work.

## Quick start

Use Python 3.12 on macOS or Linux. Run commands from the repository root.

```bash
git clone https://github.com/Omore03/nlp-multilingual-reasoning.git
cd nlp-multilingual-reasoning
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the offline checks; no API key is needed:

```bash
python -m pytest -q
python -m src.inference.runner preview --config configs/mock.yaml --question-limit 1
python -m src.inference.runner run --config configs/mock_smoke.yaml --question-limit 1 --output results/mock/local-smoke.jsonl --resume
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-matrix.jsonl --resume
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-matrix.jsonl --resume
```

Expected: 90 passing tests, eight preview prompts, four mock smoke records, 80 mock matrix records, then zero new records on resume. Mock responses and fixture selections are test placeholders, not research results. Use a fresh output name if an existing manifest reports a source or environment mismatch.

## Free API setup

The active model is **`gemma-4-31b-it` through direct Google AI Studio REST**. This project must remain free: use an unbilled Free tier project, with no paid fallback or billing upgrade. Tests run locally; hosted CI is disabled.

Copy the example settings, then edit `.env` locally:

```bash
cp .env.example .env
```

```dotenv
GOOGLE_API_KEY=your_key_here
GOOGLE_AI_STUDIO_FREE_TIER_CONFIRMED=true
```

Set the confirmation only after the key's project shows **Free** and **Set up billing** in [AI Studio Projects](https://aistudio.google.com/projects). Keep `.env` out of Git. See [model setup and settings](docs/model_decision.md).

The [run guide](docs/running.md) covers the live smoke test, team-module integration, the real pilot and resuming after quota limits. The real pilot cannot run until the reviewed data and selectors are integrated.

## Repository guide

| Path | Contents |
| --- | --- |
| `src/prompting/` | Four language templates and the final-answer convention |
| `src/inference/` | API/mock backends, input checks, logging and resume logic |
| `configs/` | Mock, live smoke and real pilot settings |
| `tests/fixtures/` | Clearly labelled synthetic data and fixed test selections |
| `data/processed/` | Reserved for reviewed real data; currently empty except for its README |
| `results/mock/` | Recorded mock runs and manifests |
| `results/live_smoke/google_direct/` | Four actual API responses to synthetic questions and the model verification receipt |
| `results/pilot_raw.jsonl` | Reserved for the real pilot; not created yet |

## Documentation

- [Run commands and recovery](docs/running.md)
- [Data, selector and output contracts](docs/integration_contract.md)
- [Team workflow](docs/team_workflow.md)
- [Received files and pending handoffs](docs/handoff_status.md)
- [Checks and live verification](docs/verification.md)
- [Submission checklist](docs/submission_checklist.md)

This repository is ready to review as work in progress. Final submission still needs the real pilot, Saad's evaluation and the remaining team deliverables. The repository is private; instructor access must be arranged before submission.
