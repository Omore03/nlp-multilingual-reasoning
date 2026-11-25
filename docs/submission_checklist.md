# Intermediate submission checklist

Updated 25 November 2026. The project lead has removed additional internal approval requirements. The published branch is `intermediate-stage`; `main` is unchanged.

## Complete

- [x] Integrate the supplied baseline implementation and preserve the original work.
- [x] Retain the fixed 18 approved demos, ten dev questions and two exclusions.
- [x] Verify seven complete saved runs, 380 scored configurations, selection/prompt/model provenance and both inherited score versions.
- [x] Adopt the audited parser policy and score completed local cutoff responses as returned; keep all raw/pre-fix evidence.
- [x] Pass 285 tests, all 14 offline config previews, data validation and mock/resume checks.
- [x] Provide results, descriptive paired statistics, uncertainty and limitations.
- [x] Provide a two-page IEEE report with Abstract, Introduction, Methodology, Results and References.
- [x] Publish code, evidence, contributions and report on `intermediate-stage`.

## Submission and meeting

- [ ] Upload the consolidated report through LMS, using one group member.
- [ ] Confirm the latest deadline/upload status and the announced meeting slot.
- [ ] Each member prepares to explain their contribution and demonstrate the code.

The latest fully visible TA notice gives 24 November, 11:59 PM; a newer message was partly obscured. This repository does not establish upload or acceptance.

## Recorded limitations and later work

The ten-question development pilot is small and establishes no strategy improvement. The 32 error-tag rows remain draft annotations, not completed independent human review. All nominal Urdu demo solutions contain English unit words. The original two exclusions stay excluded.

Hosted 31B zero-shot is optional reference work blocked by HTTP503 capacity (0/30 successful responses). No new local smoke was repeated on Ammar's Mac because Ollama is absent; the inherited local runs/receipts were independently checked. These facts are disclosed and do not leave the completed seven-run baseline unimplemented.

Dataset expansion, MGSM, diversity/complexity, four-shot prompting and final held-out evaluation remain later-stage work.
