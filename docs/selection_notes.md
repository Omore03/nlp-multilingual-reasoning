# Demonstration selection

Rayyan's random and similarity selectors are integrated. The pilot uses 18 approved demos, two examples per prompt and seed 42.

## Random baseline

Sort pool IDs, derive a per-query seed from SHA-256 of `42|id:<query_id>`, and sample two distinct candidates without replacement. No encoder is used.

## Similarity

Encode Urdu question text with `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`, revision `4328cf26390c98c5e3c738b4460a05b95f4911f5`. Normalize Unicode, keyboard letter variants, digits and whitespace. Rank cosine similarity rounded to six decimals; break ties by ascending ID.

Retrieval uses Urdu in every language condition. Only query ID and Urdu question enter the selector. The same ordered pair is reused for all four prompt conditions.

## Genuine cache and frozen plan

Rayyan supplied 30 vectors of 768 dimensions on 24 November. All 20 original selection pairs were reproduced. His original 20-demo pool included the two unapproved items; all pairs were regenerated after excluding them. Twelve ordered pairs changed.

The supplied 100 KB cache is preserved in `data/selection/vectors/`. It contains embeddings, not model weights. `approved_plan.json` records data, encoder, cache and normalized-query fingerprints. The runtime adapter validates the plan against current inputs and rejects changes. Python 3.12 and NumPy 2.3.5 replay it without downloading encoder weights.

To regenerate the identical approved plan from the supplied vectors:

```bash
python scripts/freeze_selection.py --cache data/selection/vectors/sentence-transformers_paraphrase-multilingual-mpnet-base-v2_4328cf26390c98c5e3c738b4460a05b95f4911f5.npz
```

The optional `requirements-encoder.txt` preserves Rayyan's supplied heavy-library pins. These are not needed for this pilot and were not installed during integration. A new translation requires new genuine vectors and a new experiment identity.

The submitted encoder log says CPU while its accompanying notes say MPS. We verified the supplied vectors and rankings; we did not independently repeat the encoding or certify those device/timing claims. The wrapper reads its truncation counter before encoding, so that logged zero is not evidence that no text was truncated.

## Retrieval limitations

Semantic similarity can match names, shopping topics or time units while missing mathematical structure. The [three current examples](retrieval_examples.md) use only approved candidates. Their observations are integration analysis, not an additional human review by Rayyan.

## Later methods: design only

- **Diversity:** begin with the closest candidate, then greedily choose the candidate farthest from the selected set. Decide the candidate restriction before implementing it.
- **Complexity:** rank demos by original English calculator-step count, then solution length and ID. Target solutions must never enter selection.

These methods and four-shot prompting are not implemented or reported as pilot results. The later larger experiment needs an agreed pool size, candidate restriction, additional review and separate held-out evaluation.
