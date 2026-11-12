# Data-efficient multilingual mathematical reasoning

Ammar Anees's prompting, inference, repository and integration implementation for the university NLP semester project. Few-shot in-context learning only; no fine-tuning.

**Status (12 November 2026):** implementation, offline verification and a four-condition direct Google live smoke are delivered. The real integrated pilot is pending Hussain's data and Rayyan's selectors. Saad's evaluation and final project submission remain pending. Committed mock responses are labelled separately from the four **real API responses to synthetic questions**. Both are engineering artifacts, not research results.

The initial pilot is 20 checked bilingual GSM8K training demonstrations, 10 separate bilingual training development questions, random and Urdu semantic-similarity selection, two demonstrations and four language conditions: **2 × 4 × 10 = 80** successful inference records. The larger pool, four-shot, other selectors and MGSM evaluation are later work.

## Zero-cost requirement

This project uses local development/tests and an explicitly free model API only. **Do not purchase credits, add a payment method, enable automatic top-ups, subscribe to services or rent compute for this project.** Paid model IDs are rejected. There is no paid fallback. Hosted CI automation is removed; run the local checks before merging.

The direct Google free API needs an account/key from an unbilled Free tier project, with no payment. Free capacity is limited: read your actual project quotas; the 80-record pilot may span multiple quota windows. If access/capacity is unavailable, keep the real pilot pending rather than spending money.

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

Edit `.env` locally to supply `GOOGLE_API_KEY` from a Free tier Google AI Studio project. After checking billing is disabled, set `GOOGLE_AI_STUDIO_FREE_TIER_CONFIRMED=true`. Offline operations need no key. The CLI loads this file without overriding already exported variables. Never put credentials in YAML, commands, commits or outputs.

## Executable offline checks

```bash
python -m pytest -q
python -m src.inference.runner preview --config configs/mock.yaml --question-limit 1
python -m src.inference.runner run --config configs/mock_smoke.yaml --question-limit 1 --resume
python -m src.inference.runner run --config configs/mock.yaml --resume
python -m src.inference.runner run --config configs/mock.yaml --resume
```

The preview shows eight prompts (two fixture strategies × four conditions). The mock smoke writes exactly four records, one per condition with one fixture strategy. `configs/live_smoke.yaml` uses just one fixture strategy, so its one-question smoke is exactly four conditions. The full mock matrix writes 80 successes to `results/mock/free_matrix.jsonl`. The last command should report zero new successes and leave the JSONL unchanged. `--resume` also works on an empty output path; committed examples can be inspected and resumed on the same environment.

Manifests record exact source/data/configuration and Python/package fingerprints, so an example generated elsewhere may correctly reject resumption. For a fresh local reproduction use a new output:

```bash
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-matrix.jsonl
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-matrix.jsonl --resume
```

The mock emits a prompt hash and fixed placeholder number; it does not solve or grade questions. Fixture selectors return a predefined ID table and do not implement real random or similarity selection.

## Verified free model and live smoke

`configs/pilot.yaml` and `configs/live_smoke.yaml` use **direct Google AI Studio REST** with **`gemma-4-31b-it`**, a model Google lists as free with no paid tier. The adapter rejects other models/endpoints, requires an unbilled Free tier project confirmation, checks live model metadata and uses no tools or fallback. OpenRouter is no longer the active route. Settings: temperature 0, top-p 1, seed 42, max output 2048 and native `thinkingLevel: minimal`. **Direct live access is verified: all four synthetic conditions passed.** Responses were inspected for worked solutions, Urdu text and the final marker; formal Urdu-quality/research evaluation remains separate. See [model decision](docs/model_decision.md).

Create a key at [Google AI Studio](https://aistudio.google.com/apikey). In [Projects](https://aistudio.google.com/projects), check the project associated with your key: **Billing Tier → Free**, with **Set up billing** indicating that no billing account is attached. Leave that button untouched. Then save in local `.env`:

```dotenv
GOOGLE_API_KEY=your_google_ai_studio_key
GOOGLE_AI_STUDIO_FREE_TIER_CONFIRMED=true
```

The confirmation is your explicit project-status check, not an independent billing audit by the API key. If unsure, leave it false; the adapter blocks calls. Do not attach a billing account, enter payment information or upgrade. See [Google's billing-status explanation](https://ai.google.dev/gemini-api/docs/billing#verify-billing).

```bash
python -m src.inference.runner preview --config configs/live_smoke.yaml --question-limit 1
python -m src.inference.runner run --config configs/live_smoke.yaml --question-limit 1 --resume
```

The recorded smoke completed all four conditions in five generation attempts. A no-op resume made zero new requests and left the output unchanged. The first execution of this command makes at most four successful synthetic calls plus bounded retries. Reviewed live synthetic responses are committed under `results/live_smoke/google_direct/`; other live outputs remain ignored by default. Four successful conditions automatically create `results/live_smoke/google_direct/model_verification.json`, freezing the model settings by hash and linking the actual successful records. Inspect these outputs for Urdu fluency, worked solutions, truncation and final-marker adherence before using that configuration. This engineering receipt is not a linguistic quality certification. Keep the model settings fixed for the pilot. If a setting changes, repeat the smoke using a new output under `results/live_smoke/` and set the pilot receipt path accordingly. A different provider/model requires reviewing the adapter and documentation as well and must remain explicitly free. No automatic provider/model switching is used. Historical OpenRouter attempts/configuration are retained separately and never used by these commands.

Google's actual free quotas vary by project/model and are shown in [AI Studio rate limits](https://aistudio.google.com/rate-limit). OpenRouter's previous 50/day rule does not apply. Requests are conservatively paced at least 3.1 seconds apart and capped at 40 generation attempts per invocation, including retries. Exit 3 means local-budget deferral; quota/capacity exhaustion stops without a paid fallback. Resume the identical output when the project's quota permits. The 80-record pilot may take more than one quota window. No additional keys/projects should be created to evade quotas.

## Connect the team's modules

1. Bring Hussain's reviewed files into `data/processed/demo_pool.jsonl` and `data/processed/dev.jsonl`, with his validator and dataset notes. Do not manufacture verification flags.
2. Bring Rayyan's selector modules and dependencies into `src/selection/`. Set `selector` in `configs/pilot.yaml` to the callable `module:select_examples`; the default is `src.selection.select:select_examples`. Replace `selector_version` with his encoder revision/cache identity and selector version. Add a thin adapter if his query argument differs.
3. Run their tests and all offline tests. Verify 20 checked demos, 10 separate dev questions, two valid unique demo IDs per strategy/query, Urdu-only retrieval and preserved order. See [integration contract](docs/integration_contract.md) for exact schemas.
4. Complete live smoke above, then preview and run the actual pilot:

```bash
python -m pytest -q
python -m src.inference.runner preview --config configs/pilot.yaml --question-limit 1
python -m src.inference.runner run --config configs/pilot.yaml --question-limit 1 --resume
# If the project quota permits, extend to the first 5 questions (40 pilot successes total).
python -m src.inference.runner run --config configs/pilot.yaml --question-limit 5 --resume
# When remaining free quota permits: complete remaining questions.
python -m src.inference.runner run --config configs/pilot.yaml --resume
```

The first real command writes eight live records. The next extends that identical plan to 40 successes; when quota permits, the last completes all 80. Failures/retries or other account usage may require more days. Missing production inputs, selector modules or verification receipt produce actionable errors before inference. Production paths never contain fixture content. `--question-limit` changes execution scope, not experiment identity. It always takes the first N development records in file order.

## Outputs and resumption

Successful rows include prompt, selected IDs, raw response, experiment identities, inference settings, timestamp, latency and available request/token metadata. UTF-8 is preserved. Evaluation fields are reserved for Saad and never fabricated here. Each journal has an adjacent `.manifest.json` containing resolved secret-free configuration, source/software/data identities and the frozen plan. Outputs use UTC ISO timestamps; documentation dates use PKT.

The runner checks the entire plan before inference, selects once per question/strategy, then reuses that order across all conditions. On resume it recomputes and compares the plan plus fingerprints, skips successful records and retries failures. Changed data, selection, prompt code, settings or software require a new experiment output; preserve previous journals. Freeze code and dependencies between real pilot segments. Do not merge changes while the pilot is running. Only one writer can hold an output lock.

Rows are appended, flushed and fsynced individually. An unterminated final line stops normal resumption. Inspect it, then explicitly recover:

```bash
python -m src.inference.runner run --config configs/mock.yaml --resume --repair-tail
# For a real pilot, substitute configs/pilot.yaml after reviewing the damaged file.
```

Recovery backs up the entire journal to `.corrupt-<timestamp>`, adds a newline if the final record is complete JSON, or discards only the invalid unterminated tail so it can be retried. Invalid newline-terminated lines, interior corruption, conflicting identities and duplicate successes are never silently skipped. Keep backups locally. Failure rows remain as attempt history; count unique successes, not all journal lines. Interrupting after a remote call but before a durable append can consume another free request on resume; the provider offers no exactly-once guarantee.

Exit codes: 0 for successful requested scope (including a no-op resume), 1 when this invocation wrote terminal failures, 2 for configuration/integration/journal/access errors, 3 when the free request budget defers unfinished work. A limited smoke returning 0 does not mean the 80-record pilot is complete. Auth, invalid-request, free-capacity, quota and zero-cost-policy failures stop the remaining matrix; transient errors have at most three attempts per record.

## Handoff

- [Team workflow and ownership](docs/team_workflow.md)
- [Integration schemas and final-answer convention](docs/integration_contract.md)
- [Final submission checklist](docs/submission_checklist.md)
- [Executed engineering verification](docs/verification.md)

The repository starts private. Instructor access or a later visibility decision must be resolved before final submission. This repository does not claim the real pilot or final submission is complete.
