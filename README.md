# Data-efficient multilingual mathematical reasoning

Ammar Anees's prompting, inference, repository and integration implementation for the university NLP semester project. Few-shot in-context learning only; no fine-tuning.

**Status (12 November 2026):** implementation and offline verification are delivered. The real integrated pilot is pending Hussain's data, Rayyan's selectors and authenticated model verification. Saad's evaluation and final project submission remain pending. All committed responses are deterministic **mock engineering artifacts, not research results**.

The initial pilot is 20 checked bilingual GSM8K training demonstrations, 10 separate bilingual training development questions, random and Urdu semantic-similarity selection, two demonstrations and four language conditions: **2 × 4 × 10 = 80** successful inference records. The larger pool, four-shot, other selectors and MGSM evaluation are later work.

## Setup

Use Python 3.12 on macOS or Linux (the output lock uses `fcntl`). Run commands from the repository root:

```bash
git clone https://github.com/Omore03/nlp-multilingual-reasoning.git
cd nlp-multilingual-reasoning
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` locally to supply `OPENROUTER_API_KEY` when available. Offline operations need no key. The CLI loads this file without overriding already exported variables. Never put credentials in YAML, commands, commits or outputs.

## Executable offline checks

```bash
python -m pytest -q
python -m src.inference.runner preview --config configs/mock.yaml --question-limit 1
python -m src.inference.runner run --config configs/mock_smoke.yaml --question-limit 1 --resume
python -m src.inference.runner run --config configs/mock.yaml --resume
python -m src.inference.runner run --config configs/mock.yaml --resume
```

The preview shows eight prompts (two fixture strategies × four conditions). The mock smoke writes exactly four records, one per condition with one fixture strategy. `configs/live_smoke.yaml` uses just one fixture strategy, so its one-question smoke is exactly four conditions. The full mock matrix writes 80 successes to `results/mock/matrix.jsonl`. The last command should report zero new successes and leave the JSONL unchanged. `--resume` also works on an empty output path; committed examples can be inspected and resumed on the same environment.

Manifests record exact source/data/configuration and Python/package fingerprints, so an example generated elsewhere may correctly reject resumption. For a fresh local reproduction use a new output:

```bash
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-matrix.jsonl
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-matrix.jsonl --resume
```

The mock emits a prompt hash and fixed placeholder number; it does not solve or grade questions. Fixture selectors return a predefined ID table and do not implement real random or similarity selection.

## Proposed real model and live smoke

`configs/pilot.yaml` and `configs/live_smoke.yaml` specify OpenRouter model `qwen/qwen3-235b-a22b-2507`, restricted to `deepinfra/fp8`. Temperature 0, top-p 1, generation seed 42, max output 2048 tokens; no hidden reasoning options are sent. **Live access is unverified.** Official model/provider documentation and the public endpoint catalog were checked; no API key was available. See [model decision](docs/model_decision.md).

After providing your own credential and available account credits:

```bash
python -m src.inference.runner preview --config configs/live_smoke.yaml --question-limit 1
python -m src.inference.runner run --config configs/live_smoke.yaml --question-limit 1 --resume
```

This makes at most four successful synthetic calls plus bounded retries. Live synthetic responses stay under `results/live_smoke/`. Four successful conditions automatically create `results/live_smoke/model_verification.json`, freezing the model settings by hash and linking the actual successful records. Inspect these outputs for Urdu fluency, worked solutions, truncation and final-marker adherence before using that configuration. This engineering receipt is not a linguistic quality certification. Keep the model settings fixed for the pilot. If a setting changes, repeat the smoke using a new output under `results/live_smoke/` and set the pilot receipt path accordingly. A different provider/model requires reviewing the adapter and documentation as well.

## Connect the team's modules

1. Bring Hussain's reviewed files into `data/processed/demo_pool.jsonl` and `data/processed/dev.jsonl`, with his validator and dataset notes. Do not manufacture verification flags.
2. Bring Rayyan's selector modules and dependencies into `src/selection/`. Set `selector` in `configs/pilot.yaml` to the callable `module:select_examples`; the default is `src.selection.select:select_examples`. Replace `selector_version` with his encoder revision/cache identity and selector version. Add a thin adapter if his query argument differs.
3. Run their tests and all offline tests. Verify 20 checked demos, 10 separate dev questions, two valid unique demo IDs per strategy/query, Urdu-only retrieval and preserved order. See [integration contract](docs/integration_contract.md) for exact schemas.
4. Complete live smoke above, then preview and run the actual pilot:

```bash
python -m pytest -q
python -m src.inference.runner preview --config configs/pilot.yaml --question-limit 1
python -m src.inference.runner run --config configs/pilot.yaml --question-limit 1 --resume
python -m src.inference.runner run --config configs/pilot.yaml --resume
```

The first real command writes eight live records; the next extends that identical frozen plan to all 80. Missing production inputs, selector modules or verification receipt produce actionable errors before inference. Production paths never contain fixture content. `--question-limit` changes execution scope, not experiment identity. It always takes the first N development records in file order.

## Outputs and resumption

Successful rows include prompt, selected IDs, raw response, experiment identities, inference settings, timestamp, latency and available request/token metadata. UTF-8 is preserved. Evaluation fields are reserved for Saad and never fabricated here. Each journal has an adjacent `.manifest.json` containing resolved secret-free configuration, source/software/data identities and the frozen plan. Outputs use UTC ISO timestamps; documentation dates use PKT.

The runner checks the entire plan before inference, selects once per question/strategy, then reuses that order across all conditions. On resume it recomputes and compares the plan plus fingerprints, skips successful records and retries failures. Changed data, selection, prompt code, settings or software require a new experiment output; preserve previous journals. Freeze code and dependencies between real pilot segments. Do not merge changes while the pilot is running. Only one writer can hold an output lock.

Rows are appended, flushed and fsynced individually. An unterminated final line stops normal resumption. Inspect it, then explicitly recover:

```bash
python -m src.inference.runner run --config configs/mock.yaml --resume --repair-tail
# For a real pilot, substitute configs/pilot.yaml after reviewing the damaged file.
```

Recovery backs up the entire journal to `.corrupt-<timestamp>`, adds a newline if the final record is complete JSON, or discards only the invalid unterminated tail so it can be retried. Invalid newline-terminated lines, interior corruption, conflicting identities and duplicate successes are never silently skipped. Keep backups locally. Failure rows remain as attempt history; count unique successes, not all journal lines. Interrupting after a remote call but before a durable append can incur a repeated billed request on resume; the provider offers no exactly-once guarantee.

Exit codes: 0 for successful requested scope (including a no-op resume), 1 when this invocation wrote terminal failures, 2 for configuration/integration/journal/access errors. A limited smoke returning 0 does not mean the 80-record pilot is complete. Auth, invalid-request and account-credit failures stop the remaining matrix; transient errors have at most three attempts per record.

## Handoff

- [Team workflow and ownership](docs/team_workflow.md)
- [Integration schemas and final-answer convention](docs/integration_contract.md)
- [Final submission checklist](docs/submission_checklist.md)
- [Executed engineering verification](docs/verification.md)

The repository starts private. Instructor access or a later visibility decision must be resolved before final submission. This repository does not claim the real pilot or final submission is complete.
