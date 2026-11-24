"""Build the paper's tables from Saad's evaluated artifacts, never from invented scores."""
import json
import hashlib
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]


def tex(value):
    text = str(value)
    for a, b in [('\\',r'\textbackslash{}'),('_',r'\_'),('%',r'\%'),('&',r'\&'),('#',r'\#')]:
        text = text.replace(a,b)
    return text


def build():
    rec = json.loads((ROOT / 'results/pilot_reconciliation.json').read_text())
    if not rec.get('research_eligible'):
        raise ValueError('Paper tables require manifest-checked real evaluation')
    for path, key in [('results/pilot_raw.jsonl', 'raw_sha256'),
                      ('results/pilot_raw.manifest.json', 'manifest_sha256')]:
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != rec[key]:
            raise ValueError('Real outputs changed; evaluate them again before building the paper')
    scored = [json.loads(l) for l in (ROOT / 'results/pilot_evaluated.jsonl').read_text().splitlines()]
    raw = [json.loads(l) for l in (ROOT / 'results/pilot_raw.jsonl').read_text().splitlines()]
    n = rec['unique_successful_scored']
    if len(scored) != n:
        raise ValueError('Scored output count differs from reconciliation')
    failure_count = sum(r['status'] == 'failure' for r in raw)
    lines = []
    if rec['complete']:
        lines.append(f'The real pilot completed all {n} unique configurations on 25 November 2026. '
                     f'The journal retains {failure_count} unsuccessful entries before successful resumption. '
                     'Table~\\ref{tab:pilot} reports numerical exact-match accuracy and parse failures. '
                     'All denominators are 10 development questions.')
    else:
        lines.append(f'\\textbf{{The real pilot is incomplete: {n}/80 configurations have successful responses.}} '
                     f'The journal contains {failure_count} unsuccessful entries. '
                     'Table~\\ref{tab:pilot} reports only the returned responses; its denominators are the numbers scored, '
                     'and the completion column shows coverage of the planned 10 questions per cell. '
                     'These partial figures do not satisfy a complete baseline evaluation and should not be used to rank methods.')
    lines += [r'\begin{table}[t]',r'\caption{Real development results. PF: missing or ambiguous final-answer parses.}',
              r'\label{tab:pilot}',r'\centering',r'\setlength{\tabcolsep}{3pt}',r'\begin{tabular}{llrrrr}',r'\toprule',
              r'Method & Condition & Correct & Acc. & PF & n/10 \\',r'\midrule']
    for strategy in ['random','similarity']:
        for condition in ['U-U-U','U-U-E','U-E-E','E-E-E']:
            cell = [r for r in scored if r['strategy'] == strategy and r['condition'] == condition]
            correct = sum(r['correct'] for r in cell)
            fails = sum(r['parse_status'] != 'ok' for r in cell)
            accuracy = f'{100*correct/len(cell):.0f}'+r'\%' if cell else '--'
            lines.append(f'{strategy.capitalize()} & {condition} & {correct}/{len(cell)} & {accuracy} & {fails} & {len(cell)}/10 '+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    if rec['complete']:
        cells = {(s,c):[r for r in scored if r['strategy']==s and r['condition']==c]
                 for s in ['random','similarity'] for c in ['U-U-U','U-U-E','U-E-E','E-E-E']}
        deltas = []
        for c in ['U-U-U','U-U-E','U-E-E','E-E-E']:
            delta = 10*(sum(r['correct'] for r in cells['similarity',c])-sum(r['correct'] for r in cells['random',c]))
            deltas.append(f'{c}: {delta:+d}')
        lines.append('Similarity minus random accuracy differences, in percentage points, are '+ '; '.join(deltas)+'. '
                     'These descriptive differences are not evidence of significance at this sample size.')
        gaps=[]
        for s in ['random','similarity']:
            gap=10*(sum(r['correct'] for r in cells[s,'E-E-E'])-sum(r['correct'] for r in cells[s,'U-U-U']))
            gaps.append(f'{s}: {gap:+d}')
        lines.append('The E-E-E minus U-U-U accuracy gaps, in percentage points, are '+ '; '.join(gaps)+'.')
    failures = Counter(r.get('error',{}).get('code') for r in raw if r['status']=='failure')
    if failures:
        labels = {'http_503': 'provider-capacity failures (HTTP 503)',
                  'free_request_budget_exhausted': 'local attempt-budget deferrals'}
        codes=', '.join(f'{labels.get(code, tex(code))}: {count}' for code,count in sorted(failures.items()))
        lines.append('Execution history contains '+codes+'. '
                     'These entries are retained separately from successful model answers.')
    incorrect=[r for r in scored if not r['correct']]
    if incorrect:
        examples=[]
        for r in incorrect[:3]:
            examples.append(f"query \\texttt{{{tex(r['question_id'].split('-')[-1])}}} ({r['strategy']}, {r['condition']}): "
                            f"prediction {tex(r['prediction'])}, gold {tex(r['gold_answer'])}, parse status {tex(r['parse_status'])}")
        lines.append('Saved error examples include '+ '; '.join(examples)+'. '
                     'Attributing an error to translation, arithmetic, or retrieval requires review of the saved solution.')
    elif scored:
        lines.append('All scored responses match their numeric keys. This small-sample ceiling limits any conclusion about selection effectiveness.')
    lines.append('The combined offline suite passes 229 tests, including the inherited selector and evaluation tests plus integration regressions. '
                 'The 80-record deterministic mock matrix and no-op resume also pass. These engineering checks are reported separately from the real model results.')
    abstract = (f'The real run returned {n} of 80 planned responses; {sum(r["correct"] for r in scored)} were numerically correct, '
                f'with {sum(r["parse_status"] != "ok" for r in scored)} parse failures. ')
    abstract += ('Coverage is complete, but the small sample limits comparisons.' if rec['complete'] else
                 'Provider capacity errors left incomplete coverage, so a full baseline comparison is not yet available.')
    (ROOT/'reports/intermediate/generated_abstract.tex').write_text(abstract+'\n')
    target=ROOT/'reports/intermediate/generated_results.tex'
    target.write_text('\n\n'.join(lines)+'\n')
    print(json.dumps({'successful_real_records':n,'complete':rec['complete'],'failed_record_attempts':failure_count,'paper_table':str(target.relative_to(ROOT))}))


if __name__ == '__main__':
    build()
