# Team handoff status

Updated 12 November 2026. This page records the files received and inspected locally. The teammate packages have not yet been merged into the runnable project.

## Hussain Baqar — data

Received:

- `build_pairs.py`: generates 20 demonstration and 10 dev records.
- `validate_pairs.py`: checks schema, arithmetic, overlap and review metadata.
- `dataset_notes.md`: sources, versions, licensing and known ambiguities.
- `LICENSE_GSM8K.txt`: the upstream license notice.

The generator sets every record to `translation_status: draft`, with `reviewer` and `review_date` unset. No later review evidence has been supplied. This is real-source draft data, not a synthetic test fixture.

Needed: confirmation of human review and the reviewed JSONL files with reviewer/date recorded. Automatic arithmetic checks alone cannot establish translation quality. Preserve the source notes, uncertainties and license during integration.

The supplied fields `solution_en`, `solution_ur` and `answer_number` also need mapping to the runner's `reasoning_en`, `reasoning_ur` and numeric-string `answer`. Set `verified` only from actual review evidence. See the [input contract](integration_contract.md).

## Rayyan Hasib — selection

Received:

- `rayyan_selection.zip`: random/similarity code, encoder/cache support, tests, fixtures and notes.
- `selection_handover_rayyan.html`: the earlier handover.
- `pilot_selection_report.html`: a later selection-run report.

The later report states that 55 tests passed and 20 selections were generated on Hussain's data. Those are reported results; they have not been reproduced in this repository. The ZIP does not include the later generated artifacts or all code updates described in that report.

Needed: the updated code, `selections_pilot.jsonl`, embedding cache, `retrieval_examples.md`, updated selection notes and the exact input-data version used.

Reported encoder: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`, revision `4328cf26390c98c5e3c738b4460a05b95f4911f5`. Confirm this against the delivered files before configuring the pilot. No encoder weights have been downloaded here. The test encoder must never replace the real similarity encoder in research runs.

## Ammar Anees — shared implementation

Prompting, inference, mock checks and direct Google synthetic live verification are complete. Connecting and checking the teammate packages remains pending. The production data paths and pilot output remain empty.

## Saad ur Rehman — evaluation

The parser, metrics and reporting implementation have not been supplied. The [output contract](integration_contract.md) defines his handoff, including `FINAL_ANSWER:` and the required raw records.

## Before the real pilot

1. Confirm Hussain's review status and integrate the reviewed data.
2. Reconcile Rayyan's ZIP with his later report and integrate the real selectors.
3. Run both members' checks, the project tests and a prompt preview.
4. Keep the verified model settings fixed and run the pilot within free quota.

Original teammate files remain unchanged locally. Large caches, weights and unrelated Downloads files stay outside Git.
