# Intermediate deliverable — 23 November 2026

Source: the TA email shared by Ammar. The deadline has no further extensions. The progress-meeting schedule has not yet been announced; the email does not specify a submission time or portal.

## Required deliverable

- Implemented baselines with actual results.
- Initial implementation of the proposed novelty, or a clear account of what the team will do.
- IEEE double-column report: **at most three pages, including references**.
- Sections: Abstract, Introduction, Methodology, Results and References.

## What our project needs

The approved proposal identifies **random demonstration selection as the baseline**. It proposes at least one multilingual instruction-tuned LLM; the email's general wording does not specify an additional model count for this project.

Our proposed intermediate target is the existing two-shot pilot on reviewed GSM8K training data:

| Component | Planned evidence | Current status |
| --- | --- | --- |
| Random baseline | 10 dev questions × four language conditions = 40 scored records | Not run on real data |
| Similarity comparison | Same questions and conditions = 40 scored records | Selector package received; integration pending |
| Proposed contribution | Controlled comparison of selection strategies across Urdu/English prompt arrangements | Four prompt conditions implemented; full study pending |
| Diversity and complexity | Explain the proposed algorithms and how they extend the comparison | Design notes supplied by Rayyan; production code deferred |
| Evaluation | Correct/total, accuracy and parse failures for each strategy/condition | Awaiting Saad's implementation |

The fixed model is direct Google Gemma, as documented in the [model setup](model_decision.md). Running one model under several conditions does not make them separate baseline models. If the TA expects additional baselines or a larger sample, confirm that explicitly before changing the experiment scope.

The proposed contribution is the study of selection and prompt-language effects. Do not present established similarity, diversity or complexity methods as newly invented algorithms. Describe the complete intended approach in Methodology and mark future work clearly.

The 90 passing tests and four live synthetic smoke responses establish engineering readiness. They do not provide baseline accuracy. Rayyan's reported retrieval observations are not downstream model results either.

## Suggested team milestones

These are internal targets, not additional TA deadlines.

| Target | Owner | Work |
| --- | --- | --- |
| 13–15 November | Hussain | Complete/confirm human review, resolve uncertainties and supply validated data with provenance |
| 13–15 November | Rayyan | Supply matching updated code, selections/cache, encoder identity and retrieval/design notes |
| 13–15 November | Saad | Deliver tested answer parsing, scoring and results aggregation |
| 16–18 November | Ammar + team | Integrate modules, inspect prompts and collect the 80 pilot records within free quota |
| 19–20 November | Saad + team | Reconcile counts and parse failures; prepare baseline and preliminary comparison tables |
| 21 November | All members | Assemble the concise report and contribution summary |
| 22 November | All members | Verify results, references, IEEE layout and the three-page limit; rehearse the demonstration |
| 23 November | Team | Submit by the announced deadline; follow the meeting schedule when released |

Start inference early enough to allow multiple free-quota windows. No paid fallback or automatic large-model download is authorized. See [handoff status](handoff_status.md) for current blockers.

## Report outline

| Section | Content | Approximate space |
| --- | --- | --- |
| Abstract | Question, implemented approach and measured findings once available | 0.15 page |
| Introduction | Urdu reasoning motivation, research question and proposed contribution | 0.35 page |
| Methodology | Data/review/splits, random baseline, selection methods, prompt conditions, model settings and evaluation | 1 page |
| Results | Baseline table, preliminary comparison if available, parse failures and limitations | 1 page |
| References | Dataset, model and methods actually used | 0.5 page |

This is a content budget; check the rendered IEEE document to enforce the limit. No separate title page or extra appendix should push the report beyond three pages. Use the actual IEEE template when authoring the report, rather than approximating it with a two-column layout.

For the pilot table, report the numerator and denominator alongside accuracy. Each strategy/condition has only 10 dev questions. State that this is a small development pilot and does not establish final benchmark performance or significant differences. Do not claim superiority before the paired results exist.

The results section must use authentic scored outputs. Keep placeholders out of the submitted report. Mark unfinished experiments as pending instead of filling in estimates. Cite sources used in the implementation and verify the bibliography before submission.

## Progress meeting preparation

Prepare a short demonstration of prompt preview, selection, one saved real response and its scored result. Bring the exact config/manifest and a clear account of completed work, current limitations and the next experiment. Arrange instructor access to the private repository. The meeting time remains unknown until the TA shares it.
