# Team workflow

Clone the private repository with an authorized GitHub account and follow the [README setup](../README.md#quick-start). Each developer keeps credentials in their own ignored `.env`.

## Ownership

| Member | Owned work | Suggested branch |
| --- | --- | --- |
| Ammar Anees | Prompting, inference, configs, shared setup and integration | `ammar/inference` |
| Hussain Baqar | Data, complete validator, provenance and review notes | `hussain/data-pilot` |
| Rayyan Hasib | Selectors, encoder dependencies, tests and retrieval notes | `rayyan/selectors` |
| Saad ur Rehman | Parser, evaluation, tests and research reporting | `saad/evaluation` |

Ownership includes planned modules; see [handoff status](handoff_status.md) for what has actually arrived and been integrated.

## Make a change

```bash
git switch main
git pull --ff-only
git switch -c your-name/short-change
# Make changes, then run the local tests.
python -m pytest -q
```

Inspect `git diff` and stage only the intended files. Commit, push the branch and open a pull request. Have another teammate review changes to data, prompts or selection. Do not force-push shared history.

Before merging, run the member's own checks and the project tests. If behavior changes, also run the mock smoke, full matrix and resume commands in the README. Hosted CI is disabled under the zero-spending requirement.

## Integrate teammate files

- **Hussain:** preserve his original schema, license and provenance. Use a small field adapter for the runner. Require actual review evidence before setting `verified: true` or placing data in production paths.
- **Rayyan:** use his existing selectors and tests. Pin the encoder revision, dependencies and seed policy; update `selector_version`. Keep Urdu retrieval and ordered IDs. Review his retrieval examples. Do not download large model weights automatically.
- **Saad:** provide the raw records and manifests. He adds evaluation in a separate artifact, leaving raw inference files unchanged.

The [integration contract](integration_contract.md) gives exact interfaces. The [handoff status](handoff_status.md) lists the outstanding questions.

## What belongs in Git

Track source, configs, docs, small synthetic fixtures and reviewed example outputs. Add the small real dataset only with its review and provenance notes. Preserve the GSM8K license if its data is redistributed.

Keep keys, `.env`, environments, bulk datasets, model weights, embedding caches, temporary files and recovery backups out of Git. Review live/pilot outputs for secrets and provenance before explicitly staging individual ignored files. Never force-add an entire results directory.

## Run and submit

Freeze source, data, dependencies, selectors and model settings before the real pilot. Avoid merging into a checkout with a running or unfinished pilot. Resume the same output only with matching fingerprints; use a new run for changed experiments.

Use only the free API route and existing local hardware. Wait for quota instead of purchasing capacity. Follow the [run guide](running.md), then the [submission checklist](submission_checklist.md). The owner must arrange instructor access to the private repository; visibility changes and invitations need a separate decision.
