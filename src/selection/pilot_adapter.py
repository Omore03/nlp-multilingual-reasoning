"""Serve audited, real selections frozen from Rayyan's encoder cache, without loading weights."""
import hashlib
import json
from pathlib import Path

from .encoders import normalize_urdu

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / 'data/selection/approved_plan.json'


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def provenance():
    plan = json.loads(PLAN.read_text())
    return {'kind': plan['kind'], 'encoder_id': plan['encoder_id'], 'encoder_revision': plan['encoder_revision'],
            'embedding_cache_sha256': plan['embedding_cache_sha256'],
            'frozen_plan_sha256': hashlib.sha256(PLAN.read_bytes()).hexdigest(),
            'review_receipt_sha256': hashlib.sha256((ROOT / 'data/review/review_receipt.json').read_bytes()).hexdigest()}


def select_examples(query, pool, k, strategy, seed):
    plan = json.loads(PLAN.read_text())
    if plan.get('kind') != 'real_frozen_selection' or _digest(pool) != plan['pool_canonical_sha256']:
        raise ValueError('Pool differs from the audited real frozen selection; regenerate the plan')
    if set(query) != {'id', 'question_ur'}:
        raise ValueError('Only the query ID and Urdu question may cross the selector boundary')
    query_hash = hashlib.sha256(normalize_urdu(query['question_ur']).encode()).hexdigest()
    rows = [p for p in plan['pairs'] if (p['question_id'], p['strategy'], p['seed'], p['shot_count']) ==
            (query['id'], strategy, seed, k)]
    if len(rows) != 1 or rows[0]['question_ur_sha256'] != query_hash:
        raise ValueError('Query/settings differ from the genuine frozen selection')
    return list(rows[0]['demo_ids'])


select_examples.provenance = provenance
