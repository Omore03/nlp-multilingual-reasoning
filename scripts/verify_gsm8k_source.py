"""Check supplied pilot questions and numeric keys against a local pinned GSM8K train file."""
import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://raw.githubusercontent.com/openai/grade-school-math/3101c7d5072418e28b9008a6636bde82a006892c/grade_school_math/data/train.jsonl'


def main(path):
    raw = Path(path).read_bytes()
    source = [json.loads(l) for l in raw.decode().splitlines()]
    normalize = lambda text: ' '.join(text.split())
    indexed = {normalize(r['question']): r for r in source}
    rows = []
    for name in ['data/processed/demo_pool.jsonl', 'data/processed/dev.jsonl', 'data/review/excluded_demos.jsonl']:
        rows += [json.loads(l) for l in (ROOT/name).read_text().splitlines()]
    matches = []
    for row in rows:
        original = indexed[normalize(row['question_en'])]
        assert Decimal(original['answer'].split('####')[-1].strip().replace(',', '')) == Decimal(str(row['answer']))
        matches.append({'id': row['id'], 'question_match': 'exact' if row['question_en'] == original['question'] else 'whitespace-normalized', 'numeric_key_match': True})
    receipt = {'checked_on': '2026-11-25', 'source_url': SOURCE, 'source_commit': '3101c7d5072418e28b9008a6636bde82a006892c', 'raw_file_sha256': hashlib.sha256(raw).hexdigest(), 'source_rows': len(source), 'question_matches': len(matches), 'exact_question_matches': sum(m['question_match']=='exact' for m in matches), 'numeric_key_matches': len(matches), 'scope': 'English questions (whitespace-normalized where needed) and numeric keys only; not independent Urdu or full worked-solution review.', 'items': matches}
    (ROOT/'data/review/source_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print({k:v for k,v in receipt.items() if k not in ['source_url','items','scope']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--train', required=True)
    main(parser.parse_args().train)
