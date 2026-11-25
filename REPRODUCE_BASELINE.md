# Reproduce the baseline

25 November 2026. Run from the repository root. Offline scoring requires neither credentials nor model weights. The local package includes raw responses, manifests, both inherited scoring versions, reviewed data and the genuine small embedding cache.

## Offline checks

Use Python 3.12 and `requirements.txt`; see README setup. Rayyan's collection environment is recorded in `evidence/baseline_2026_11_25/environment.txt`.

```bash
python -m pytest -q
python -m src.data.validate
python scripts/audit_baseline.py
python scripts/compare_arms.py --out docs/model_comparison.md
python scripts/baseline_statistics.py
python scripts/build_baseline_report.py
```

Expected: 285 tests; valid 18/10 data and two exclusions; 380 records, 15 scoring gains, zero losses and seven newly parsed wrong answers. The audit checks inherited file hashes, reconstructs run/plan/record hashes and all prompts, reproduces v1, rescores with the current parser, and requires all scored rows to match bundled v2. New evaluations go only to `results/verified/`; raw files and inherited scores stay unchanged. New reconciliations include parser version/hash, marker list and evaluated-file hash.

Individual rescoring into a new folder:

```bash
python -m src.evaluation.report --raw results/gemma3_4b/pilot_raw.jsonl --dev data/processed/dev.jsonl --manifest results/gemma3_4b/pilot_raw.manifest.json --out-dir results/verified/manual_4b
```

Folders: `results/` (31B two-shot), `results/gemma3_4b/`, `results/gemma3_4b_zeroshot/`, `results/gemma3_4b_seed43/`, `results/gemma3_4b_seed44/`, `results/gemma3_1b/`, `results/gemma3_1b_zeroshot/`. The flat layout matches the configs/scripts; the bundle nested these files by model/method. Source receipt records the map and every hash.

Each arm retains `scored_before_parser_fix/`. The v1 parser is preserved as evidence, never installed over current source. `results/archive/aborted_gemma3_1b/` holds the stopped six-row attempt and is excluded from scores, as are synthetic smoke and mock records.

## Preview and mock resume

```bash
python -m src.inference.runner preview --config configs/pilot_ollama_gemma3_4b.yaml --question-limit 1
python -m src.inference.runner preview --config configs/zeroshot_ollama_gemma3_4b.yaml --question-limit 1
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-repro.jsonl --resume
python -m src.inference.runner run --config configs/mock.yaml --output results/mock/local-repro.jsonl --resume
```

Expected: eight two-shot and three zero-shot previews; 80 mock successes then zero new records. Choose a new mock filename after a source/environment change. All 14 configs previewed successfully without inference.

```bash
python scripts/freeze_selection.py --cache data/selection/vectors/sentence-transformers_paraphrase-multilingual-mpnet-base-v2_4328cf26390c98c5e3c738b4460a05b95f4911f5.npz
```

This regenerates the identical approved selection plan from genuine cached vectors without loading encoder weights.

## Optional local smoke

Not repeated during integration: Ollama is absent on this Mac. Protocol tests and inherited receipts are not a fresh live smoke. If Ollama and the exact weights are already installed:

```bash
python -m src.inference.runner run --config configs/ollama_gemma3_4b_smoke.yaml --output results/live_smoke/ollama_4b_repro/smoke.jsonl --question-limit 1
```

4B full digest: `68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7`; 1B: `97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c`. The backend refuses changed digests and remote endpoints. A fresh real run needs a separate config pointing at its matching new smoke receipt and a fresh output. Do not rerun valid inference merely to change scoring.

## Hosted zero-shot reference

The fixed free Google model and existing user-confirmed unbilled project were used. Repeated HTTP503 failures left zero successful responses out of 30, so the attempt stopped. Failure journal/manifest and sanitized receipt are retained. No paid fallback or billing change was used. Do not retry capacity errors in a loop. Resume only when free capacity returns and full frozen source/software identity matches; otherwise choose a fresh output. The API key does not independently establish project billing or available quota.

## Report build

With Tectonic 0.17.0 available:

```bash
python scripts/build_baseline_report.py
mkdir -p output/pdf
cd reports/baseline_2026_11_25
tectonic --outdir ../../output/pdf main.tex
```

Reviewed copy: `reports/baseline_2026_11_25/baseline_report.pdf`. IEEEtran conference class and complete source are included. `reports/intermediate/` remains unchanged; the legacy report builder reproduces its inputs. Completed inference is evaluated offline after source changes rather than bypassing fingerprints for resume.

## Submission status and later work

The project lead has removed additional internal approval requirements. The intermediate baseline uses the audited parser and completed-output cutoff policy, focuses selection comparisons on 4B, and retains 31B/1B as references. It is published on `intermediate-stage`; `main` is unchanged. Upload and meeting preparation remain to be done.

Error tags remain draft annotations, not independent human review. Dataset expansion, MGSM, diversity/complexity and four-shot are deferred. No LMS submission or main merge has occurred.
