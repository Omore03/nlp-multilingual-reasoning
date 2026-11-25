"""Split each strategy/condition cell into reasoning errors and format failures.

Reads Saad's evaluated JSONL (never re-scores) and adds descriptive categories:

  correct        parse ok and numerically correct
  wrong_answer   parse ok but wrong number; the cause requires response review
  cut_off        hit the output-token limit (finish_reason=length), e.g. repetition loops
  no_marker      finished, but no FINAL_ANSWER-style marker with a number
  ambiguous      finished, but markers disagree or give several numbers

Two flags are counted alongside (they overlap the categories):
  answer_only    historical name for fewer than ANSWER_ONLY_TOKENS output tokens (a heuristic)
  off_language   the response's main script differs from the target-question script (a heuristic)

Format failures = cut_off + no_marker + ambiguous. Exact match is unchanged; this is diagnosis only.

lenient_correct is a permissive diagnostic, NOT an independent score: it re-reads the number after the LAST literal
FINAL_ANSWER (colon optional), ignoring the parser's generic 'final answer:' phrases. It shows how many
exact-match failures may be formatting-related. It also includes every official correct record and accepts the first
number in a segment; it therefore cannot independently certify parser correctness or sound reasoning.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.evaluation.answer_parser import find_numbers, normalize_text, to_decimal  # noqa: E402

ANSWER_ONLY_TOKENS = 40
CATEGORIES = ('correct', 'wrong_answer', 'cut_off', 'no_marker', 'ambiguous')
FLAGS = ('answer_only', 'off_language', 'lenient_correct')
LITERAL_MARKER = re.compile(r'FINAL_ANSWER\s*:?', re.IGNORECASE)
CONDITION_ORDER = ('U-U-U', 'U-U-E', 'U-E-E', 'E-E-E')
ARABIC = re.compile(r'[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]')
LATIN = re.compile(r'[A-Za-z]')


def response_script(text):
    # Ignore the marker itself; compare letters only.
    text = text.replace('FINAL_ANSWER', '')
    arabic, latin = len(ARABIC.findall(text)), len(LATIN.findall(text))
    if not arabic and not latin:
        return 'none'
    return 'ur' if arabic >= latin else 'en'


def lenient_prediction(text):
    hits = list(LITERAL_MARKER.finditer(normalize_text(text).replace('*', '')))
    if not hits:
        return None
    rest = normalize_text(text).replace('*', '')[hits[-1].end():].strip()
    numbers = find_numbers(rest.splitlines()[0]) if rest else []
    return numbers[0] if numbers else None


def categorize(rec):
    if rec['correct']:  # Always agree with Saad's exact-match score.
        return 'correct'
    if rec.get('finish_reason') == 'length':
        return 'cut_off'
    if rec['parse_status'] == 'missing':
        return 'no_marker'
    if rec['parse_status'] == 'ambiguous':
        return 'ambiguous'
    return 'correct' if rec['correct'] else 'wrong_answer'


def flags(rec):
    tokens = (rec.get('usage') or {}).get('completion_tokens')
    target = 'ur' if rec['condition'].startswith('U') else 'en'
    script = response_script(rec['raw_response'])
    lenient = lenient_prediction(rec['raw_response'])
    return {'answer_only': isinstance(tokens, int) and tokens < ANSWER_ONLY_TOKENS,
            'off_language': script not in ('none', target),
            'lenient_correct': bool(rec['correct']) or (lenient is not None and lenient == to_decimal(rec['gold_answer']))}


def breakdown(evaluated_path):
    rows = [json.loads(line) for line in Path(evaluated_path).read_text(encoding='utf-8').splitlines() if line.strip()]
    cells = {}
    for rec in rows:
        for key in [(rec['strategy'], rec['condition']), (rec['strategy'], 'ALL'), ('ALL', rec['condition']), ('ALL', 'ALL')]:
            cell = cells.setdefault(key, Counter())
            cell['n'] += 1
            cell[categorize(rec)] += 1
            for name, on in flags(rec).items():
                cell[name] += int(on)
    strategies = sorted({r['strategy'] for r in rows}, key=lambda s: (s == 'ALL', ('random', 'similarity', 'none').index(s)
                                                                      if s in ('random', 'similarity', 'none') else 9))
    order = lambda k: ((strategies + ['ALL']).index(k[0]), (CONDITION_ORDER + ('ALL',)).index(k[1]))
    table = []
    for key in sorted(cells, key=order):
        c = cells[key]
        table.append({'strategy': key[0], 'condition': key[1], 'n': c['n'], **{k: c[k] for k in CATEGORIES},
                      'format_failures': c['cut_off'] + c['no_marker'] + c['ambiguous'], **{k: c[k] for k in FLAGS}})
    return table


def markdown(table):
    head = ('| Strategy | Condition | n | Correct | Wrong answer | Cut off | No marker | Ambiguous | '
            'Format failures | Answer only | Off-language | Lenient correct |')
    lines = [head, '|' + '---|' * 12]
    for r in table:
        lines.append(f"| {r['strategy']} | {r['condition']} | {r['n']} | {r['correct']} | {r['wrong_answer']} | "
                     f"{r['cut_off']} | {r['no_marker']} | {r['ambiguous']} | {r['format_failures']} | "
                     f"{r['answer_only']} | {r['off_language']} | {r['lenient_correct']} |")
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--evaluated', required=True, type=Path, help="Saad's <prefix>_evaluated.jsonl")
    parser.add_argument('--out-prefix', required=True, type=Path, help='Writes <prefix>.md and <prefix>.csv')
    args = parser.parse_args(argv)
    table = breakdown(args.evaluated)
    md = markdown(table)
    args.out_prefix.with_suffix('.md').write_text(md, encoding='utf-8')
    with args.out_prefix.with_suffix('.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    print(md)


if __name__ == '__main__':
    main()
