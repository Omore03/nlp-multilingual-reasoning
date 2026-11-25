"""Descriptive, question-paired baseline statistics from verified saved outputs."""
import json
from math import sqrt
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from compare_arms import load_arm, cell, paired_counts, mcnemar_exact


def wilson(correct, n):
    z = 1.959963984540054
    p = correct/n
    den = 1 + z*z/n
    mid = (p+z*z/(2*n))/den
    half = z*sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0, mid-half), min(1, mid+half)]


def main():
    arms = {'31b': load_arm('results'), '4b': load_arm('results/gemma3_4b'),
            '1b': load_arm('results/gemma3_1b')}
    cells, comparisons = [], []
    for name, rows in arms.items():
        for condition in ('U-U-U', 'U-U-E', 'U-E-E', 'E-E-E'):
            for strategy in ('random', 'similarity'):
                group = cell(rows, strategy, condition)
                correct = sum(r['correct'] for r in group)
                cells.append({'model':name,'condition':condition,'strategy':strategy,
                              'correct':correct,'n':len(group),'wilson_95':wilson(correct,len(group))})
            b,c = paired_counts(cell(rows,'similarity',condition),cell(rows,'random',condition))
            comparisons.append({'comparison':'similarity vs random seed42','model':name,'condition':condition,
                                'first_only_correct':b,'second_only_correct':c,'n':10,
                                'delta_points':10*(b-c),'p_unadjusted':mcnemar_exact(b,c)})
        path = ROOT / f'results/gemma{4 if name=="31b" else 3}_{name}_zeroshot/pilot_reconciliation.json'
        if not path.exists() or not json.loads(path.read_text()).get('complete'):
            continue
        zero = load_arm(path.parent)
        for condition in ('U-U-U','U-U-E','U-E-E','E-E-E'):
            z = cell(zero,'none','U-U-E' if condition=='U-E-E' else condition)
            for strategy in ('random','similarity'):
                two = cell(rows,strategy,condition)
                b,c = paired_counts(two,z)
                comparisons.append({'comparison':f'two-shot {strategy} vs zero-shot','model':name,'condition':condition,
                                    'first_only_correct':b,'second_only_correct':c,'n':10,
                                    'delta_points':10*(b-c),'p_unadjusted':mcnemar_exact(b,c)})
    data={'date':'2026-11-25','cells':cells,'paired_comparisons':comparisons,
          'interpretation':'Exploratory unadjusted exact two-sided McNemar tests. Ten paired questions per cell; no independent-observation pooling across conditions or strategies. Wilson intervals are per cell, not across repeated configurations.'}
    (ROOT/'evidence/baseline_2026_11_25/statistics.json').write_text(json.dumps(data,indent=2)+'\n')
    lines=['# Baseline paired comparisons','',data['interpretation'],'',
           '| Comparison | Model | Condition | Difference (pp) | First only | Second only | p |',
           '|---|---|---|---|---|---|---|']
    for r in comparisons:
        lines.append(f"| {r['comparison']} | {r['model']} | {r['condition']} | {r['delta_points']:+d} | {r['first_only_correct']} | {r['second_only_correct']} | {r['p_unadjusted']:.3f} |")
    lines += ['', '## Per-cell uncertainty', '', '| Model | Method | Condition | Correct/n | Wilson 95% interval |', '|---|---|---|---|---|']
    for r in cells:
        lo,hi=r['wilson_95']
        lines.append(f"| {r['model']} | {r['strategy']} | {r['condition']} | {r['correct']}/{r['n']} | {100*lo:.1f}% to {100*hi:.1f}% |")
    (ROOT/'docs/baseline/statistics.md').write_text('\n'.join(lines)+'\n')
    print(f'Wrote {len(cells)} cell intervals and {len(comparisons)} paired comparisons.')


if __name__=='__main__':
    main()
