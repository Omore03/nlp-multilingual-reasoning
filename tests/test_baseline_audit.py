"""Regressions for parser boundaries and stale/mismatched analysis artifacts."""
import importlib.util
import json
from pathlib import Path

import pytest

from src.evaluation.answer_parser import parse_answer


@pytest.mark.parametrize('text', [
    'NOT_FINAL_ANSWER: 70', 'FINAL_ANSWERING 70', 'xFINAL_ANSWER 70',
    'FINAL_ANSWER_suffix: 70',
])
def test_embedded_marker_is_not_an_explicit_answer(text):
    assert parse_answer(text).status == 'missing'


@pytest.mark.parametrize('text,prediction,status', [
    ('FINAL_ANSWER: -۲.۵', '-2.5', 'ok'),
    ('FINAL_ANSWER: ٨\nLater calculation: 2 + 2 = 4', '8', 'ok'),
    ('FINAL_ANSWER: 8 or 9', None, 'ambiguous'),
    ('FINAL_ANSWER: 8\nUse FINAL_ANSWER: followed by the number', '8', 'ok'),
    ('FINAL_ANSWER: 8\nFINAL_ANSWER: 9', '9', 'ok'),
    ('There are 70 items; no terminal marker.', None, 'missing'),
])
def test_primary_marker_adversarial_cases(text, prediction, status):
    result = parse_answer(text)
    assert (result.prediction, result.status) == (prediction, status)


def comparison_module():
    path = Path(__file__).resolve().parents[1] / 'scripts/compare_arms.py'
    spec = importlib.util.spec_from_file_location('baseline_comparison_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_comparison_rejects_stale_artifacts(tmp_path):
    compare = comparison_module()
    (tmp_path / 'pilot_reconciliation.json').write_text(json.dumps({
        'complete': True, 'research_eligible': True, 'unique_successful_scored': 1,
        'raw_sha256': '0'*64, 'manifest_sha256': '0'*64, 'evaluated_sha256': '0'*64}))
    for name in ('pilot_raw.jsonl', 'pilot_raw.manifest.json', 'pilot_evaluated.jsonl'):
        (tmp_path / name).write_text('{}\n')
    with pytest.raises(ValueError, match='changed|stale'):
        compare.load_arm(tmp_path)


def test_paired_comparison_rejects_different_questions():
    compare = comparison_module()
    with pytest.raises(ValueError, match='paired'):
        compare.paired_counts([{'question_id':'a', 'correct':True}],
                              [{'question_id':'b', 'correct':False}])
