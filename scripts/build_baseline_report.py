"""Build the consolidated baseline paper table from provenance-checked evaluated files."""
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from compare_arms import load_arm, cell


def main():
    specs=[('Gemma 4 31B','results'),('Gemma 3 4B','results/gemma3_4b'),
           ('Gemma 3 4B','results/gemma3_4b_seed43'),('Gemma 3 4B','results/gemma3_4b_seed44'),
           ('Gemma 3 4B','results/gemma3_4b_zeroshot'),('Gemma 3 1B','results/gemma3_1b'),
           ('Gemma 3 1B','results/gemma3_1b_zeroshot')]
    audit=json.loads((ROOT/'evidence/baseline_2026_11_25/audit.json').read_text())
    if audit['total_scored']!=380 or audit['total_gained']!=15 or audit['total_lost']!=0:
        raise ValueError('Report text needs review after changed baseline evidence')
    lines=[r'\begin{table}[t]',r'\caption{Numerical exact match on ten development questions per language cell. Zero-shot U-E-E shares the U-U-E prompt and is not rerun.}',
           r'\label{tab:baseline}',r'\centering',r'\setlength{\tabcolsep}{2.6pt}',r'\small',
           r'\begin{tabular}{llrrrrr}',r'\toprule',r'Model & Method & UUU & UUE & UEE & EEE & Total \\',r'\midrule']
    n=correct=0
    for label,folder in specs:
        rows=load_arm(folder)
        n+=len(rows);correct+=sum(r['correct'] for r in rows)
        for strategy in ('random','similarity','none'):
            selected=[r for r in rows if r['strategy']==strategy]
            if not selected:continue
            seed=selected[0]['seed']
            method=('zero-shot' if strategy=='none' else f'random {seed}' if strategy=='random' else 'similarity')
            counts=[]
            for condition in ('U-U-U','U-U-E','U-E-E','E-E-E'):
                group=cell(rows,strategy,condition)
                if not group and strategy=='none' and condition=='U-E-E':counts.append('shared')
                else:
                    if len(group)!=10:raise ValueError('Every scored cell must have ten matched questions')
                    counts.append(str(sum(r['correct'] for r in group)))
            lines.append(f"{label.replace('Gemma ','')} & {method} & "+' & '.join(counts)+f" & {sum(r['correct'] for r in selected)}/{len(selected)} "+r'\\')
    if n!=380:raise ValueError('Incomplete consolidated table')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    dest=ROOT/'reports/baseline_2026_11_25/generated_results.tex'
    dest.write_text('\n'.join(lines)+'\n')
    print(json.dumps({'configurations':n,'numerically_correct':correct,'table':str(dest.relative_to(ROOT))}))


if __name__=='__main__':main()
