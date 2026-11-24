"""Inspect genuine cached neighbours in the approved pool without encoding or API calls."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.selection.similarity import EmbeddingCache, rank_pool
from scripts.freeze_selection import CACHE_SHA, sha


def main():
    cache_path = next((ROOT / 'data/selection/vectors').glob('*.npz'))
    if sha(cache_path) != CACHE_SHA:
        raise ValueError('Supplied vector fingerprint changed')
    cache = EmbeddingCache(cache_path.parent, cache_path.stem)

    class NoEncoding:
        def encode(self, texts):
            raise ValueError('Missing genuine vector')

    pool = [json.loads(l) for l in (ROOT/'data/processed/demo_pool.jsonl').read_text().splitlines()]
    dev = {r['id']: r for r in map(json.loads, (ROOT/'data/processed/dev.jsonl').read_text().splitlines())}
    demos = {r['id']: r for r in pool}
    observations = {
        'gsm8k-train-19b0d3572fbe': 'The target needs subtraction followed by addition. Grades and student-budget examples share school or name vocabulary, but their percentage calculations differ. Similarity is not a direct mathematical-structure score.',
        'gsm8k-train-4e78856e0b87': 'The target subtracts change from cash and divides by unit price. The leading shopping/food examples multiply quantities and sum totals instead; topic overlap does not imply the same operations.',
        'gsm8k-train-1d58b8a27f49': 'The target combines a Friday percentage increase with four ordinary days. The remaining budget and hourly-pay neighbours share percentages or time, but do not demonstrate that complete structure.'
    }
    lines = ['# Approved-pool retrieval examples', '', 'Recomputed on 25 November from Rayyan\'s genuine pinned encoder cache, after excluding demos 4 and 5. Scores are cosine similarity rounded to six decimals. Observations below are integration analysis; Rayyan has not separately approved them. These are retrieval examples, not downstream accuracy results.']
    for qid, observation in observations.items():
        q = dev[qid]
        lines += ['', '## '+qid, '', q['question_en'], '', q['question_ur'], '', '| Rank | Demo ID | Cosine | English question |', '| --- | --- | --- | --- |']
        for n, (did, score) in enumerate(rank_pool(q['question_ur'], pool, NoEncoding(), cache)[:5],1):
            lines.append(f"| {n} | `{did}` | {score:.6f} | {demos[did]['question_en'].replace('|','/')} |")
        lines += ['', observation]
    (ROOT/'docs/retrieval_examples.md').write_text('\n'.join(lines)+'\n')
    print('Wrote three genuine approved-pool neighbour examples')


if __name__ == '__main__':
    main()
