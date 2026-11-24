"""Freeze Rayyan's genuine selections from existing encoder vectors; never downloads weights."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from src.selection import select_examples
from src.selection.similarity import EmbeddingCache, text_key

ENCODER = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
REVISION = '4328cf26390c98c5e3c738b4460a05b95f4911f5'
CACHE_SHA = '99727733efb8f7706c2ec2c2033849d613db52247206863e62dc357e70df463d'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def freeze(cache_path):
    pool_path = ROOT / 'data/processed/demo_pool.jsonl'
    dev_path = ROOT / 'data/processed/dev.jsonl'
    pool = [json.loads(l) for l in pool_path.read_text().splitlines()]
    dev = [json.loads(l) for l in dev_path.read_text().splitlines()]
    cache_path = Path(cache_path)
    if sha(cache_path) != CACHE_SHA:
        raise ValueError('Cache fingerprint differs from the audited Rayyan submission')
    with np.load(cache_path, allow_pickle=False) as arrays:
        if arrays['vectors'].shape != (30, 768) or not np.isfinite(arrays['vectors']).all():
            raise ValueError('Unexpected cached vector shape or values')
    cache = EmbeddingCache(cache_path.parent, cache_path.stem)
    if any(text_key(r['question_ur']) not in cache._store for r in pool + dev):
        raise ValueError('A question changed; supplied vectors do not cover the new text')

    class NoEncoding:
        cache_key = cache_path.stem

        def encode(self, texts):
            raise ValueError('Missing genuine vector; obtain a new reviewed encoder cache')

    pairs = []
    for query in dev:
        for strategy in ('random', 'similarity'):
            ids = select_examples({'id': query['id'], 'question_ur': query['question_ur']}, pool,
                                  2, strategy, 42, encoder=NoEncoding(), cache=cache)
            pairs.append({'question_id': query['id'], 'question_ur_sha256': text_key(query['question_ur']),
                          'strategy': strategy, 'seed': 42, 'shot_count': 2, 'demo_ids': ids})
    output = {'kind': 'real_frozen_selection', 'owner': 'Rayyan Hasib', 'integration': 'Ammar Anees',
              'encoder_id': ENCODER, 'encoder_revision': REVISION, 'embedding_cache_sha256': CACHE_SHA,
              'method': 'Rayyan production random and cosine selectors replayed on supplied genuine cached vectors',
              'pool_records': len(pool), 'dev_records': len(dev), 'pool_canonical_sha256': canonical_sha(pool),
              'input_files': {'demo_pool.jsonl': sha(pool_path), 'dev.jsonl': sha(dev_path)},
              'excluded_demo_ids': ['gsm8k-train-4ed90b091532', 'gsm8k-train-2e8fc28b2be6'],
              'pairs': pairs}
    path = ROOT / 'data/selection/approved_plan.json'
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'pairs': len(pairs)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', required=True)
    freeze(parser.parse_args().cache)
