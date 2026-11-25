"""Side-by-side comparison of evaluated model arms (descriptive; built only from Saad's evaluated files).

Each arm is a results folder holding <prefix>_evaluated.jsonl and <prefix>_reconciliation.json.
Only complete, manifest-checked (research-eligible) arms are accepted.
Similarity vs random uses the exact two-sided McNemar test on paired questions, as in
docs/evaluation_plan.md; with 10 questions per cell it is reported, not relied on.
"""
import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ('U-U-U', 'U-U-E', 'U-E-E', 'E-E-E')
_spec = importlib.util.spec_from_file_location('error_breakdown', ROOT / 'scripts/error_breakdown.py')
eb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eb)


def load(path):
    return [json.loads(l) for l in Path(path).read_text(encoding='utf-8').splitlines() if l.strip()]


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n)


def load_arm(folder, prefix='pilot'):
    folder = ROOT / folder
    rec = json.loads((folder / f'{prefix}_reconciliation.json').read_text())
    if not (rec.get('research_eligible') and rec.get('complete')):
        raise ValueError(f'{folder} is not a complete, manifest-checked real evaluation')
    rows = [json.loads(l) for l in (folder / f'{prefix}_evaluated.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    if len(rows) != rec['unique_successful_scored']:
        raise ValueError(f'{folder}: evaluated rows differ from reconciliation')
    return rows


def cell(rows, strategy, condition):
    return [r for r in rows if r['strategy'] == strategy and r['condition'] == condition]


def fmt(rows):
    return f"{sum(r['correct'] for r in rows)}/{len(rows)}" if rows else '—'


def build(arms):
    out = ['# Model-arm comparison: Gemma 4 31B, Gemma 3 4B, Gemma 3 1B', '',
           'Same 10 dev questions, 18-item pool, frozen selections, prompts and decoding in every two-shot arm; '
           'only the model changes. Zero-shot arms use the same questions with no demonstrations. '
           'Each cell is correct/10. Built by `scripts/compare_arms.py` from the evaluated files.', '',
           '## Exact-match accuracy', '',
           '| Arm | Strategy | ' + ' | '.join(CONDITIONS) + ' | All |', '|' + '---|' * 7]
    loaded = [(name, folder, load_arm(folder)) for name, folder in arms]
    for name, _, rows in loaded:
        for strategy in [s for s in ('random', 'similarity', 'none') if any(r['strategy'] == s for r in rows)]:
            cells = []
            for c in CONDITIONS:
                x = cell(rows, strategy, c)
                if not x and strategy == 'none' and c == 'U-E-E':
                    cells.append('= U-U-E')  # identical prompt at zero shots
                else:
                    cells.append(fmt(x))
            label = 'zero-shot' if strategy == 'none' else strategy
            out.append(f"| {name} | {label} | " + ' | '.join(cells) + f" | {fmt([r for r in rows if r['strategy'] == strategy])} |")
    out += ['', 'U-E-E is not run at zero shots: with no demonstrations its prompt is the same as U-U-E.', '',
            '## Similarity minus random (paired)', '',
            'b = questions only similarity solved; c = questions only random solved; p = exact two-sided McNemar.', '',
            '| Arm | Condition | Similarity − random (points) | b | c | p |', '|---|---|---|---|---|---|']
    for name, _, rows in loaded:
        if not any(r['strategy'] == 'similarity' for r in rows):
            continue
        for c in CONDITIONS:
            sim = {r['question_id']: r['correct'] for r in cell(rows, 'similarity', c)}
            ran = {r['question_id']: r['correct'] for r in cell(rows, 'random', c)}
            b = sum(sim[q] and not ran[q] for q in sim)
            cc = sum(ran[q] and not sim[q] for q in sim)
            delta = 100 * (sum(sim.values()) - sum(ran.values())) // len(sim)
            out.append(f'| {name} | {c} | {delta:+d} | {b} | {cc} | {mcnemar_exact(b, cc):.3f} |')
    seed_runs = [(42, ROOT / 'results/gemma3_4b')] + [(k, ROOT / f'results/gemma3_4b_seed{k}') for k in (43, 44)]
    seed_runs = [(k, f) for k, f in seed_runs if (f / 'pilot_reconciliation.json').exists()]
    if len(seed_runs) > 1:
        runs = {k: load_arm(f.relative_to(ROOT)) for k, f in seed_runs}
        sim = next((rows for name, _, rows in loaded if name == 'Gemma 3 4B (two-shot)'), None)
        out += ['', '## Random selection across seeds (Gemma 3 4B)', '',
                'Seeds 43 and 44 change only the random demonstration pairs (generation seed stays 42). '
                'The spread shows how far random can move by chance; a strategy gap smaller than it is not evidence.', '',
                '| Condition | ' + ' | '.join(f'Random seed {k}' for k in runs) + ' | Random range | Similarity |',
                '|' + '---|' * (len(runs) + 3)]
        for c in CONDITIONS + ('ALL',):
            vals = [sum(r['correct'] for r in rows if r['strategy'] == 'random' and (c == 'ALL' or r['condition'] == c))
                    for rows in runs.values()]
            n = 40 if c == 'ALL' else 10
            simv = sum(r['correct'] for r in sim if r['strategy'] == 'similarity' and (c == 'ALL' or r['condition'] == c)) if sim else None
            out.append(f'| {c} | ' + ' | '.join(f'{v}/{n}' for v in vals) + f' | {min(vals)}–{max(vals)} | '
                       + (f'{simv}/{n}' if simv is not None else '—') + ' |')
    out += ['', '## Two examples vs zero-shot (same model)', '',
            '| Model | Condition | Zero-shot | Two-shot random | Two-shot similarity |', '|---|---|---|---|---|']
    by_model = defaultdict(dict)
    for name, _, rows in loaded:
        model = name.replace(' zero-shot', '').replace(' (two-shot)', '')
        by_model[model]['zero' if 'zero-shot' in name and '(two-shot)' not in name else 'two'] = rows
    for model, parts in by_model.items():
        if 'zero' not in parts or 'two' not in parts:
            continue
        for c in CONDITIONS:
            z = cell(parts['zero'], 'none', 'U-U-E' if c == 'U-E-E' else c)
            out.append(f"| {model} | {c} | {fmt(z)}{' (U-U-E)' if c == 'U-E-E' else ''} | "
                       f"{fmt(cell(parts['two'], 'random', c))} | {fmt(cell(parts['two'], 'similarity', c))} |")
    out += ['', '## Reasoning errors vs format failures (all strategies pooled per arm and condition)', '',
            'Wrong answer = a parsed but wrong number. Format failures = cut off at the 2048-token limit, no marker, '
            'or ambiguous marker. Answer only = under 40 output tokens. Off-language = solution mainly in the other '
            'script than the target question. Lenient = independent cross-check (number after the last literal '
            'FINAL_ANSWER, colon optional); since parser version 2 it should equal Correct. See `scripts/error_breakdown.py`.', '',
            '| Arm | Condition | n | Correct | Lenient | Wrong answer | Cut off | No/ambiguous marker | Answer only | Off-language |',
            '|' + '---|' * 10]
    for name, folder, rows in loaded:
        table = eb.breakdown(ROOT / folder / 'pilot_evaluated.jsonl')
        for t in table:
            if t['strategy'] == 'ALL' and t['condition'] != 'ALL':
                out.append(f"| {name} | {t['condition']} | {t['n']} | {t['correct']} | {t['lenient_correct']} | {t['wrong_answer']} | {t['cut_off']} | "
                           f"{t['no_marker'] + t['ambiguous']} | {t['answer_only']} | {t['off_language']} |")
    before_after = [(name, folder) for name, folder, _ in loaded] + [
        (f'Gemma 3 4B random, seed {k}', f'results/gemma3_4b_seed{k}') for k in (43, 44)]
    before_after = [(n, f) for n, f in before_after if (ROOT / f / 'scored_before_parser_fix/pilot_evaluated.jsonl').exists()]
    if before_after:
        out += ['', '## Parser change (version 2, pending approval): scores before and after', '',
                'Same raw responses, re-scored. Version 2 reads the number after the last FINAL_ANSWER that has one '
                '(colon optional) and falls back to the earlier rule only when there is none. '
                'See `docs/parser_change_2026-11-25.md`.', '',
                '| Run | Correct before | Correct after | Gained | Lost | Parse failures before | after |',
                '|---|---|---|---|---|---|---|']
        for name, folder in before_after:
            old = {r['record_id']: r for r in load(ROOT / folder / 'scored_before_parser_fix/pilot_evaluated.jsonl')}
            new = {r['record_id']: r for r in load(ROOT / folder / 'pilot_evaluated.jsonl')}
            if old.keys() != new.keys():
                raise ValueError(f'{folder}: before/after records differ')
            gained = sum(new[k]['correct'] and not old[k]['correct'] for k in new)
            lost = sum(old[k]['correct'] and not new[k]['correct'] for k in new)
            out.append(f"| {name} | {sum(r['correct'] for r in old.values())}/{len(old)} | {sum(r['correct'] for r in new.values())}/{len(new)} | "
                       f"{gained} | {lost} | {sum(r['parse_status'] != 'ok' for r in old.values())} | "
                       f"{sum(r['parse_status'] != 'ok' for r in new.values())} |")
    out += ['', '## Caveats', '',
            '- 10 questions per cell: one question is 10 points. An exact McNemar test reaches p < 0.05 only if at '
            'least 6 questions differ and all go the same way (6–0 gives p = 0.031; 5–0 gives 0.063; 6–1 gives 0.125).',
            '- All questions are GSM8K training items, so memorisation cannot be ruled out, most of all for the 31B model.',
            '- 4B and 1B are 4-bit (Q4_K_M) local builds; 31B is the hosted full model. Size is not the only difference.',
            '- One selection seed (42), except the 4B random seed check (42, 43, 44). The deferred diversity/complexity '
            'selectors, 4-shot prompts and MGSM are not included.', '']
    return '\n'.join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='results/model_comparison.md')
    args = parser.parse_args(argv)
    arms = [('Gemma 4 31B (two-shot)', 'results'),
            ('Gemma 3 4B (two-shot)', 'results/gemma3_4b'),
            ('Gemma 3 4B zero-shot', 'results/gemma3_4b_zeroshot'),
            ('Gemma 3 1B (two-shot)', 'results/gemma3_1b'),
            ('Gemma 3 1B zero-shot', 'results/gemma3_1b_zeroshot')]
    arms = [(n, f) for n, f in arms if (ROOT / f / 'pilot_reconciliation.json').exists()]
    text = build(arms)
    (ROOT / args.out).write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
