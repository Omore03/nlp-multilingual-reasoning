"""Update the human-readable verification record from reconciled real outputs."""
import hashlib
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]


def main():
    raw = ROOT/'results/pilot_raw.jsonl'
    rec = json.loads((ROOT/'results/pilot_reconciliation.json').read_text())
    if not rec['research_eligible'] or rec['raw_sha256'] != hashlib.sha256(raw.read_bytes()).hexdigest():
        raise ValueError('Evaluate the current genuine journal before documenting it')
    rows = [json.loads(l) for l in raw.read_text().splitlines()]
    scored = [json.loads(l) for l in (ROOT/'results/pilot_evaluated.jsonl').read_text().splitlines()]
    n = rec['unique_successful_scored']
    errors = Counter(r.get('error',{}).get('code') for r in rows if r['status']=='failure')
    usage = Counter()
    for r in rows:
        if r['status']=='success':
            usage.update({k:v for k,v in (r.get('usage') or {}).items() if isinstance(v,(int,float))})
    status = 'Complete' if rec['complete'] else 'Incomplete'
    lines = ['# Verification', '', 'Updated 25 November 2026 (PKT). Real results and engineering checks are separate.', '', '## Integrated checks', '', '| Check | Outcome |','| --- | --- |', '| Offline suite, including a fresh GitHub clone | 229 passed |', '| Approved data | 18 demos, 10 dev, two excluded demos; 30 disjoint IDs |', '| Arithmetic and review ledger | Passed |', '| Pinned GSM8K source | All 30 questions and keys match; five questions use normalized whitespace |', '| Original Rayyan selections | All 20 reproduced from genuine vectors |', '| Approved frozen selections | 20 pairs regenerated; no rejected IDs; byte-identical regeneration |', '| Real prompt preview | Eight prompts inspected; target gold excluded |', '| Integrated mock matrix | 80 successes; resume adds zero records |', '', 'The mock matrix and manifest are preserved in `results/mock/integrated_matrix.*`. They are engineering fixtures and never enter research accuracy.', '', '## Real pilot', '', f'**{status}: {n}/80 unique successful responses.** The data consist of 10 questions, two strategies and four language conditions, with two examples per prompt.', '', f'- Correct numerical answers among scored responses: {sum(r["correct"] for r in scored)}/{len(scored)}.', f'- Parse failures: {sum(r["parse_status"] != "ok" for r in scored)}.', f'- Failed record attempts retained in history: {rec["failed_calls"]}.', f'- Missing configurations: {len(rec["missing_configurations"])}.', f'- Reconciliation balanced: {str(rec["totals_balance"]).lower()}; matching real manifest required.', f'- Run identity: `{rec["run_id"]}`.', f'- Journal SHA-256: `{rec["raw_sha256"]}`.', f'- Manifest SHA-256: `{rec["manifest_sha256"]}`.', '', 'The final table is [pilot_summary.md](../results/pilot_summary.md). The full journal, manifest, evaluated responses and reconciliation are tracked separately. Failures followed by success count once; failed calls are not model answers.', '', 'Recorded terminal error codes: '+(', '.join(f'`{k}`: {v}' for k,v in sorted(errors.items())) or 'none')+'.', '', 'Collection is dated 25 November, after the TA\'s 23 November deadline. Partial coverage does not establish a complete baseline; even complete coverage is only a small development pilot, not final benchmark performance.', '', '## Model and spending constraint', '', 'The configured native Google model is `gemma-4-31b-it`, with the frozen settings in `configs/pilot.yaml`. Requests use the existing project that the user confirmed as Free tier with no billing attached. No paid fallback or billing change was made. The API does not provide measured dollar cost, so no billing measurement is claimed.', '', 'Successful-response token metadata: `'+json.dumps(dict(usage),sort_keys=True)+'`. Failed requests may not report usage; these totals are not a complete account of all provider-side computation.', '', 'The four-condition synthetic live smoke from 12 November remains historical access evidence under `results/live_smoke/google_direct/`. Its journal SHA-256 is `61495daddeb16955910167c95e74a1806193d2522e8e7ae3f8a654691b04e5ec`. It is not included in research metrics. The dated model-catalog snapshot also remains historical.', '', '## Submission and later work', '', 'The report uses the actual IEEEtran class; its rendered page count must stay within three including references. Upload and meeting attendance remain team actions. The repo is public as observed on 25 November; this work does not change visibility. Hosted CI remains disabled.', '', 'Correct/re-review the two excluded demos before reuse. Larger reviewed experiments, deferred selectors, four-shot prompting and separate MGSM evaluation remain future work. See [submission checklist](submission_checklist.md).']
    (ROOT/'docs/verification.md').write_text('\n'.join(lines)+'\n')
    p=ROOT/'README.md';s=p.read_text()
    start='**Status: 25 November 2026.**'
    a=s.index(start);b=s.index('\n\n',a)
    paragraph=f'{start} The reviewed dataset, real selectors and evaluator are integrated. **229 offline tests pass.** The real pilot has **{n}/80 successful configurations**'+(' and is complete.' if rec['complete'] else '; collection is incomplete because free-provider capacity is intermittent.')+' See [results](results/pilot_summary.md), [verification](docs/verification.md) and the [IEEE report](reports/intermediate/intermediate_report.pdf).'
    p.write_text(s[:a]+paragraph+s[b:])
    print({'successful':n,'complete':rec['complete'],'updated':['README.md','docs/verification.md']})


if __name__ == '__main__':
    main()
