"""Validate the integrated reviewed subset using Hussain's arithmetic checker and recorded decisions."""
import json
from pathlib import Path
import hashlib
import unicodedata
from .hussain_validator import decimal, evaluate, NUM
from src.inference.contracts import load_records

ROOT = Path(__file__).resolve().parents[2]


def validate():
    demos = load_records(ROOT / 'data/processed/demo_pool.jsonl', True)
    dev = load_records(ROOT / 'data/processed/dev.jsonl')
    excluded = [json.loads(l) for l in (ROOT / 'data/review/excluded_demos.jsonl').read_text().splitlines()]
    receipt = json.loads((ROOT / 'data/review/review_receipt.json').read_text())
    decisions = {r['id']: r for r in receipt['items']}
    calculations = {r['id']: r for r in json.loads((ROOT / 'data/review/calculations.json').read_text())}
    if len(demos) != 18 or len(dev) != 10 or len(excluded) != 2:
        raise ValueError('Reviewed pilot must contain 18 demos, 10 dev questions and two excluded demos')
    rows = demos + dev + excluded
    if len({r['id'] for r in rows}) != 30 or set(decisions) != {r['id'] for r in rows}:
        raise ValueError('Review ledger and the disjoint data IDs do not match')
    for row in rows:
        decision = decisions[row['id']]
        if row in excluded:
            if decision['approved'] or row['verified']:
                raise ValueError('Excluded demos must remain unapproved')
        elif decision['approved'] is not True:
            raise ValueError('Production record is not approved by the recorded review')
        expected_id = 'gsm8k-train-' + hashlib.sha256(row['question_en'].encode()).hexdigest()[:12]
        if row['id'] != expected_id:
            raise ValueError('Source question does not match its content-based ID')
        for lang in ('en', 'ur'):
            if row['question_' + lang] != unicodedata.normalize('NFC', row['question_' + lang]):
                raise ValueError('Non-NFC question text')
        numbers = [sorted({decimal(m.group()) for m in NUM.finditer(row['question_' + lang])}) for lang in ('en', 'ur')]
        if numbers[0] != numbers[1]:
            raise ValueError('English/Urdu question digits differ')
        source = calculations[row['id']]
        for step in source['calculations']:
            if evaluate(step['expression']) != decimal(step['result']):
                raise ValueError('Hussain arithmetic validation failed')
        if decimal(source['calculations'][-1]['result']) != decimal(row['answer']):
            raise ValueError('Final answer differs from the worked calculation')
    return {'approved_demos': len(demos), 'approved_dev': len(dev), 'excluded_demos': len(excluded),
            'unique_disjoint_ids': len(rows), 'arithmetic_checks': 'passed',
            'human_review_evidence': 'signed document plus Hussain confirmation reported by Ammar on 2026-11-25'}


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
