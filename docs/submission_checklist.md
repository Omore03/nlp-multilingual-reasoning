# Baseline review checklist

Updated 25 November 2026. The latest fully visible TA notice gives 24 November, 11:59 PM; a newer message is partly obscured. Confirm the latest deadline, upload status and meeting slot with the team.

## Completed locally

- [x] Integrate Rayyan's 35-file patch on an isolated feature branch; preserve main and all unrelated files.
- [x] Keep 18 approved demos, ten dev questions and two exclusions unchanged.
- [x] Audit selection, prompts, seed handling, model metadata and inference controls.
- [x] Independently reconcile all seven completed journals and 380 scored records.
- [x] Reproduce both inherited parser versions; inspect all 15 numerical gains and seven newly parsed wrong answers.
- [x] Record current parser provenance and preserve raw/pre-fix evidence.
- [x] Run 285 tests, all 14 offline config previews, data validation and mock/resume.
- [x] Prepare 32 draft error tags and a consolidated IEEE report for team review.

## Remaining decisions/actions

- [ ] D1: team agrees the primary model (4B recommended; 31B/1B reference arms retained).
- [ ] D2: Saad/team ratify scoring completed cutoff outputs as returned.
- [ ] D3: Saad/team approve the parser policy; draft numerical audit is not human sign-off.
- [ ] D6: team approves the consolidated report/extra arms and each member understands their work.
- [ ] Saad/Rayyan review the draft error tags; Hussain reviews language issues before any later data change.
- [ ] Ammar approves any remote push, PR or main integration.
- [ ] Team submits via the required channel, confirms pilot sufficiency, and attends the meeting.

Optional reference: hosted 31B zero-shot is blocked by HTTP503 capacity (0/30 responses). Local smoke was not repeated on this Mac because Ollama is absent. Neither is represented as completed.

Dataset expansion (D5), MGSM (D4), diversity/complexity selectors, four-shot and final held-out evaluation remain deferred. No submission, push or merge has occurred.
