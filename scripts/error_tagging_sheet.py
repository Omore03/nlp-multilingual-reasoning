"""Build a manual error-tagging worksheet from evaluated runs (for human review; assigns no tags itself).

Rows: every non-correct answer of the selected two-shot runs, or a fixed per-cell sample. Each row shows the
question, gold and predicted answers, the automatic category from scripts/error_breakdown.py, the two
demonstrations shown, and the arithmetic operations of the question and of each demonstration (from Hussain's
reviewed data/review/calculations.json). The operation columns support the tag "copied the operation from an
example"; dev operations are used here for analysis only and never reach the selector or the prompt.
Reviewers fill the empty tag columns.
"""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('error_breakdown', ROOT / 'scripts/error_breakdown.py')
eb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eb)

TAGS = ('arithmetic slip', 'wrong plan / misread question', 'copied the operation from an example',
        'language or translation issue', 'format only (right number, unparsed)', 'repetition loop / cut off', 'other')
OPS = {'+': '+', '-': '−', '*': '×', '/': '÷'}
CONDITION_ORDER = ('U-U-U', 'U-U-E', 'U-E-E', 'E-E-E')


def operations(calcs):
    seq = []
    for step in calcs:
        seq += [OPS[ch] for ch in re.sub(r'(?<![\d)])-', '', step['expression']) if ch in OPS]
    return ' '.join(seq)


def load(path):
    return [json.loads(l) for l in Path(path).read_text(encoding='utf-8').splitlines() if l.strip()]


def rows_for(label, folder, per_cell, ops, pool, dev):
    recs = load(ROOT / folder / 'pilot_evaluated.jsonl')
    bad = sorted((r for r in recs if not r['correct']),
                 key=lambda r: (r['strategy'], CONDITION_ORDER.index(r['condition']), r['question_id']))
    if per_cell:
        kept, seen = [], {}
        for r in bad:
            key = (r['strategy'], r['condition'])
            if seen.get(key, 0) < per_cell:
                kept.append(r)
                seen[key] = seen.get(key, 0) + 1
        bad = kept
    out = []
    for r in bad:
        d1, d2 = (r['demo_ids'] + [None, None])[:2]
        out.append({
            'model': label, 'strategy': r['strategy'], 'condition': r['condition'], 'question_id': r['question_id'],
            'question_en': dev[r['question_id']]['question_en'], 'gold': r['gold_answer'], 'prediction': r['prediction'],
            'parse_status': r['parse_status'], 'auto_category': eb.categorize(r), 'finish_reason': r.get('finish_reason'),
            'output_tokens': (r.get('usage') or {}).get('completion_tokens'),
            'question_ops': ops.get(r['question_id'], ''),
            'demo1_id': d1, 'demo1_ops': ops.get(d1, ''), 'demo1_question_en': pool.get(d1, {}).get('question_en', ''),
            'demo2_id': d2, 'demo2_ops': ops.get(d2, ''), 'demo2_question_en': pool.get(d2, {}).get('question_en', ''),
            'response': r['raw_response'],
            'tag_primary': '', 'tag_secondary': '', 'notes': '', 'reviewer': ''})
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', default='results/error_tagging')
    args = parser.parse_args(argv)
    calcs = json.loads((ROOT / 'data/review/calculations.json').read_text())
    ops = {c['id']: operations(c['calculations']) for c in calcs}
    pool = {d['id']: d for d in load(ROOT / 'data/processed/demo_pool.jsonl')}
    dev = {d['id']: d for d in load(ROOT / 'data/processed/dev.jsonl')}
    rows = (rows_for('Gemma 3 4B', 'results/gemma3_4b', 0, ops, pool, dev)       # every 4B error
            + rows_for('Gemma 3 1B', 'results/gemma3_1b', 2, ops, pool, dev))    # 2 per cell sample
    out = ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'error_tagging_sheet.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    n4 = sum(r['model'] == 'Gemma 3 4B' for r in rows)
    guide = f"""# Error-tagging worksheet

`error_tagging_sheet.csv` (UTF-8, opens in Excel/Sheets) has {len(rows)} rows: all {n4} non-correct two-shot answers from
Gemma 3 4B, plus a fixed sample of {len(rows) - n4} from Gemma 3 1B (the first 2 by question ID in each strategy/condition cell).
No tags are filled in; they need a human reading of the `response` column.

Columns to use: `question_ops` (operations in the reviewed solution of the question), `demo1_ops` / `demo2_ops` (the two
solved examples shown), `auto_category` (from `scripts/error_breakdown.py`), `response` (the model's full answer).

Fill `tag_primary` (and optionally `tag_secondary`) with one of:

{chr(10).join('- ' + t for t in TAGS)}

"copied the operation from an example" fits when the response follows an example's operation sequence where the question
needs a different one (compare `question_ops` with `demo1_ops` / `demo2_ops`). Operations come from Hussain's reviewed
`data/review/calculations.json`, are for analysis only, and are never used for selection or prompting.
Regenerate with `python scripts/error_tagging_sheet.py`.
"""
    (out / 'README.md').write_text(guide, encoding='utf-8')
    print(guide)


if __name__ == '__main__':
    main()
