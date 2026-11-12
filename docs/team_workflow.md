# Team workflow

The initial repository is private at `https://github.com/Omore03/nlp-multilingual-reasoning`. Collaborator invitations and instructor access must be handled by the repository owner when agreed; no invitations or visibility changes are part of this delivery.

Clone with your authorized GitHub account, then follow the README's Python 3.12 virtual environment and dependency commands. Keep `.env` local and use `.env.example` as the variable-name contract. Never send keys through commits or PR comments. Each developer obtains their own credential; offline tests need none.

## File ownership and branches

| Owner | Files | Suggested branch |
| --- | --- | --- |
| Ammar Anees | `src/prompting/`, `src/inference/`, `configs/`, shared setup/testing and integration documentation | `ammar/inference` |
| Hussain Baqar | `data/processed/`, future `src/data/validate.py`, `docs/dataset_notes.md`, dataset tests | `hussain/data-pilot` |
| Rayyan Hasib | future `src/selection/`, selector tests, `docs/selection_notes.md`, encoder dependency additions | `rayyan/selectors` |
| Saad ur Rehman | future `src/evaluation/`, evaluation tests, evaluation plan and actual pilot summaries | `saad/evaluation` |

Suggested workflow:

```bash
git switch main
git pull --ff-only
git switch -c hussain/data-pilot
# Add the member's actual reviewed submission, then run checks.
python -m pytest -q
git add <reviewed-files>
git diff --cached
git commit -m "Integrate reviewed bilingual pilot data"
git push -u origin hussain/data-pilot
```

Open a pull request to `main` and have another teammate review the actual files. Do not force-push, rewrite shared history or merge generated code without tests. Keep scope to the initial pilot. Before every commit inspect status and staged changes for credentials, personal files, downloads, weights and generated artifacts.

## Integrate submissions from WhatsApp

Hussain's and Rayyan's completed submissions have not yet been supplied to this workspace. Preserve their originals and provenance when received; do not silently rewrite them to fit the runner.

For Hussain: add reviewed real JSONL to the reserved production paths, his full validator and dataset notes (sources, licenses/versions, translation/review evidence, split membership and no overlap). Run his validator and tests. The runner accepts optional dev `verified`, but real demo verification must be true based on actual review. Record uncertainties instead of inventing review.

For Rayyan: bring his existing random and similarity modules, tests and notes into his owned paths; add his dependencies to requirements and refresh the dependency snapshot if necessary. Connect the configured callable via a thin wrapper if needed. Use Urdu retrieval for every condition. Record encoder revision, cache identity, deterministic tie-breaking and seed policy in `selector_version` and selection notes. Run his deterministic/ranking/ID checks and manually inspect his three retrieval examples.

For Saad: give him the raw schema, mock outputs and literal `FINAL_ANSWER:` contract. He supplies parser, metrics, reporting tests and final evaluation plan. He must read only successful unique experiments and join the actual dev answer keys without altering raw inference files. Mock placeholders are for parser/engineering checks only and must never enter a research accuracy table.

## Before merging and before the real pilot

Required for every merge: `python -m pytest -q` passes offline, updated member tests pass, schemas remain compatible, and no secrets or unrelated assets are staged. Hosted CI automation has been removed to avoid any billable runner usage; local tests are the required merge check. A teammate reviews changed prompt/data/selector behavior. Retest the CLI's preview, four-condition mock coverage and 80-record matrix after integration changes.

Before real inference: establish 20 verified demos/10 reviewed dev records, disjoint IDs, two genuine selectors, current free-model access and four successful live smoke conditions. Run preview, review prompts and returned ID order, then run the one-question real smoke and full/resumed pilot using the commands in README. Freeze data, source, software, selector version and model settings for that pilot. No merges into a running checkout. Fingerprint rejection requires preserving prior output and starting a separate reviewed experiment, not bypassing compatibility checks.

## Tracking policy

Track reviewed source, configuration, documentation, small synthetic fixtures, representative mock journals/manifests and local test configuration. Track the 30 reviewed real records and provenance notes after checking dataset permissions and team review. Do not commit bulk downloaded datasets, original PDFs, embedding caches, model weights, environments, temporary renders or secrets.

Live and real result directories are ignored initially to prevent accidental publication. After the team reviews provenance/secrets, explicitly stage the small authentic pilot journal and manifest with `git add -f results/pilot_raw.jsonl results/pilot_raw.manifest.json`; similarly select actual live-smoke receipts/outputs or Saad's summaries. Do not blanket-force-add all results. Keep failed attempts and manifests for traceability. Backups ending `.corrupt-*`, output locks and temporary files stay local. Restore/resume a damaged tail only after inspecting the backup policy in README.

## Handoff and submission

Use `docs/submission_checklist.md` to distinguish Ammar's implementation from integrated pilot and final submission. Current blockers are the actual WhatsApp data/selector packages, a free OpenRouter API credential/access and Saad's evaluation. Repository publication alone does not complete the team project. Resolve instructor access or repository visibility before final submission, with an explicit owner decision.

## Zero project spending

Use existing local hardware and the fixed free model route only. No payment method, credit purchase, top-up, paid fallback, subscription or rented compute is required. At the unfunded free tier, plan at least two quota days for 80 records and resume after quota resets. Keep the model/settings fixed between days. Do not restore hosted Actions or purchase extra capacity as a workaround; local `python -m pytest -q` is the verification gate.
