# Submission checklist

## Ammar implementation and repository delivery

- [x] Modular prompting/inference package and YAML configs.
- [x] Four two-shot prompt conditions, fixed demo identity/order and Urdu retrieval boundary.
- [x] Real API adapter, deterministic mock, incremental logging, retry and resume safeguards.
- [x] Separate synthetic fixtures and mock outputs; no synthetic production inputs/results.
- [x] Reproducible setup, integration contract, ownership/team workflow, model evidence.
- [x] Final verification report and private GitHub push verified (see docs/verification.md).
- [x] Four-condition authenticated direct Google synthetic smoke and model freeze completed; no paid route used.

Ammar's code and offline handoff can be complete while live integration is pending. The selected live configuration remains explicitly unverified until the credentialed smoke succeeds.

## Real integrated initial pilot - pending

- [ ] Receive Hussain's 20 checked demonstrations and 10 separate development questions.
- [ ] Receive complete validator, source/version/license/translation notes and human review evidence.
- [ ] Receive Rayyan's real random/similarity selectors, tests, exact encoder revision and cache identity.
- [ ] Validate disjoint IDs, schema, valid unique ordered two-demo returns and Urdu retrieval for all conditions.
- [x] Complete four-condition live smoke; inspect output and freeze model settings (direct Google, synthetic fixture).
- [ ] Run one real dev question through both selectors and all conditions (8 records).
- [ ] Complete/reconcile 80 unique successful real records, or document terminal failures and compute/access blockers.
- [ ] Preserve `results/pilot_raw.jsonl` and its manifest, prompts, selected IDs and provenance.
- [ ] Integrate Saad's parser, metrics, reporting and their passing tests.
- [ ] Reconcile evaluation totals/parse failures and label pilot metrics as diagnostics only.

## Final semester submission - pending

- [ ] Complete the team's later approved work: larger demonstration pool, four-shot, diversity/complexity and final paired MGSM evaluation.
- [ ] Complete paired comparisons, qualitative error analysis and dataset/translation checks through the assigned owners.
- [ ] Review actual research tables/figures and distinguish pilot diagnostics from final evidence.
- [ ] Reproduce commands from a clean clone and preserve exact experiment provenance.
- [ ] Review dataset/result sharing permissions, citations, limitations and university requirements.
- [ ] Resolve instructor access or decide repository visibility explicitly; the repository is initially private.
- [ ] Confirm all team modules, authentic results and final report are present before declaring submission ready.

No fixture result, mock response, passing engineering test or private GitHub repository is evidence that the real pilot or final research submission is complete.

## Direct Google free-only acceptance

- [x] Fixed native Gemma model/endpoint; no paid or Gemini fallback, tools or billing changes.
- [x] Google API key and explicit unbilled Free tier project confirmation required before calls.
- [x] Native payload/metadata/visible-response handling, retries, pacing/budget and resumability tested offline.
- [x] Hosted CI automation remains removed; tests run locally.
- [x] Direct Google key/project configured and explicitly confirmed Free tier; key excluded from Git.
- [x] Four genuine direct Urdu/English synthetic smoke outputs inspected; matching receipt preserved.
- [ ] Complete the real pilot using actual project quota, preserving model/settings across quota windows.

The earlier OpenRouter key was authenticated, but six attempts returned upstream shared-pool HTTP 429. That history is not successful direct Google verification.
