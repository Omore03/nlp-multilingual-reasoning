# Intermediate report

The TA requires implemented baselines and results, an initial novelty implementation or clear plan, and an IEEE double-column report of at most three pages including references. Required sections: Abstract, Introduction, Methodology, Results and References.

The deadline was 23 November. This integration and real collection are dated 25 November, with no claim of an extension or earlier submission.

## Current scope

Random selection is the proposal's baseline. Similarity is the implemented comparison. Both use the same 10 development questions, four language conditions and two demonstrations from the approved 18-item pool: 80 configurations total. Diversity and complexity remain designs. One model under several conditions is still one model.

The contribution is the controlled Urdu/English selection-and-language study. Cosine retrieval itself is established. Ten questions support preliminary diagnosis; this document cannot guarantee that the TA will accept that sample as sufficient.

## Report artifacts

`reports/intermediate/main.tex` uses the actual IEEEtran conference class. `generated_results.tex` is built from manifest-checked real results by `scripts/build_report_inputs.py`. The final PDF and build instructions are in the same report folder.

Results must state coverage, correct/total, accuracy, parse failures and limitations. Failed API calls remain in the raw history and are not successful answers. Tests and mock runs are separate engineering evidence.

## Progress demonstration

Show the approved dataset, one query's ordered selections across all four conditions, a saved real response and its evaluated record. Bring the exact configuration/manifest and describe the next experiment. Confirm the meeting time and submission channel with the TA.
