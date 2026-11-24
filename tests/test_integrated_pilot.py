"""Integration regressions: reviewed pool, genuine frozen selection and evaluation provenance."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import pytest

from src.data.validate import validate
from src.inference import runner
from src.selection.pilot_adapter import select_examples
from src.evaluation.answer_parser import parse_answer
from src.evaluation.report import reconcile, is_complete, build_report

ROOT = Path(__file__).resolve().parents[1]


def test_reviewed_real_plan_uses_18_approved_demos_and_no_exceptions():
    assert validate()['approved_demos'] == 18
    manifest = runner.prepare(runner.load_config('configs/pilot.yaml'))
    assert manifest['expected_records'] == 80
    excluded = {'gsm8k-train-4ed90b091532', 'gsm8k-train-2e8fc28b2be6'}
    grouped = {}
    for p in manifest['plan']:
        assert not excluded.intersection(p['demo_ids'])
        grouped.setdefault((p['question_id'], p['strategy']), []).append(p['demo_ids'])
    assert len(grouped) == 20 and all(len(v) == 4 and all(ids == v[0] for ids in v) for v in grouped.values())
    assert manifest['identity']['selector']['encoder_revision'] == '4328cf26390c98c5e3c738b4460a05b95f4911f5'


@pytest.mark.parametrize('value', ['1200', '۱۲۰۰', '١٢٠٠'])
def test_actual_terminal_marker_with_bilingual_digits(value):
    parsed = parse_answer('Worked solution.\nFINAL_ANSWER: ' + value)
    assert parsed.status == 'ok' and parsed.prediction == '1200'


def test_frozen_selector_rejects_changed_text_and_gold_leakage():
    pool = [json.loads(l) for l in (ROOT / 'data/processed/demo_pool.jsonl').read_text().splitlines()]
    q = json.loads((ROOT / 'data/processed/dev.jsonl').read_text().splitlines()[0])
    minimal = {'id': q['id'], 'question_ur': q['question_ur']}
    with pytest.raises(ValueError):
        select_examples({**minimal, 'answer': q['answer']}, pool, 2, 'random', 42)
    with pytest.raises(ValueError):
        select_examples({**minimal, 'question_ur': 'changed'}, pool, 2, 'random', 42)
    altered = deepcopy(pool); altered[0]['answer'] = '10000'
    with pytest.raises(ValueError):
        select_examples(minimal, altered, 2, 'random', 42)


def test_empty_and_conflicting_evaluations_are_incomplete():
    _, summary = reconcile([], {'q': Decimal(2)})
    assert not is_complete(summary, [])
    base = {'question_id':'q','condition':'U-U-U','strategy':'random','shot_count':2,'seed':42,
            'model_id':'m','demo_ids':['a','b'],'prompt':'p','raw_response':'FINAL_ANSWER: 2'}
    _, summary = reconcile([base, {**base,'raw_response':'FINAL_ANSWER: 3'}], {'q':Decimal(2)}, conditions=('U-U-U',), strategies=('random',))
    assert not is_complete(summary, [])


def test_real_evaluation_requires_manifest_and_rejects_mock_or_foreign_records(tmp_path):
    m = runner.prepare(runner.load_config('configs/pilot.yaml'))
    manifest = tmp_path / 'manifest.json'; manifest.write_text(json.dumps(m))
    q = m['plan'][0]
    record = {**q,'run_id':m['run_id'],'model_id':m['resolved_configuration']['model']['model_id'],
              'mode':'live','data_kind':'real','status':'success','raw_response':'FINAL_ANSWER: 768',
              'data_fingerprints':m['identity']['data'],'inference_settings':m['resolved_configuration']['model']}
    raw = tmp_path / 'raw.jsonl'; raw.write_text(json.dumps(record)+'\n')
    dev = ROOT / 'data/processed/dev.jsonl'
    with pytest.raises(ValueError):
        build_report(raw, dev, tmp_path / 'no_manifest')
    result = build_report(raw, dev, tmp_path / 'partial', manifest_path=manifest)
    assert result['reconciliation']['expected_configurations'] == 80
    assert result['reconciliation']['unique_successful_scored'] == 1
    assert not result['reconciliation']['complete']
    for changes in ({'mode':'mock'},{'run_id':'foreign'},{'model_id':'other'}, {'prompt':'changed'}):
        raw.write_text(json.dumps({**record, **changes})+'\n')
        with pytest.raises(ValueError):
            build_report(raw, dev, tmp_path / 'reject', manifest_path=manifest)
