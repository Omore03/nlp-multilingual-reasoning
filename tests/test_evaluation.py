import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evaluation.answer_parser import AMBIGUOUS, MISSING, OK, find_numbers, parse_answer, to_decimal
from evaluation.metrics import CONDITIONS, full_summary, gold_answers, is_correct, score_record, summarize
from evaluation.report import build_report, contract_problems, main, reconcile

FIXTURES = Path(__file__).parent / "fixtures"
RAW_FIXTURE = FIXTURES / "eval_raw_responses.jsonl"
DEV_FIXTURE = FIXTURES / "eval_dev.jsonl"


@pytest.mark.parametrize(
    "response, expected",
    [
        ("#### 1200", "1200"),
        ("#### 1,200", "1200"),
        ("#### $1,200 dollars", "1200"),
        ("#### 1,234,567", "1234567"),
        ("#### 85.0", "85"),
        ("#### 0.5", "0.5"),
        ("#### .5", "0.5"),
        ("#### -15", "-15"),
        ("#### −15", "-15"),
        ("#### ‏-15", "-15"),
        ("#### 25%", "25"),
        ("#### 85 kg", "85"),
        ("#### 85.", "85"),
        ("#### 85۔", "85"),
        ("Work: 4 * 3 = 12, 97 - 12 = 85\n#### 85", "85"),
        ("**Final Answer:** 85", "85"),
        ("The final answer is 42.", "42"),
        ("final answer: 42", "42"),
        ("#### 42\nSome closing remark with 7 words.", "42"),
        ("#### 768\n#### 768", "768"),
        ("Final answer: 768\n#### 768", "768"),
    ],
)
def test_parses_western_formats(response, expected):
    result = parse_answer(response)
    assert result.status == OK
    assert result.prediction == expected


@pytest.mark.parametrize(
    "response, expected",
    [
        ("#### ۷۶۸", "768"),
        ("#### ٧٦٨", "768"),
        ("#### -۱۵", "-15"),
        ("#### ١٬٢٠٠", "1200"),
        ("#### ۱,۲۰۰", "1200"),
        ("#### ٢٫٥", "2.5"),
        ("#### ۵۰٪", "50"),
        ("کل سبزیاں 768 ہیں۔\nحتمی جواب: ٧٦٨", "768"),
        ("آخری جواب: ۸۵ کلوگرام", "85"),
        ("حتمی جواب: 85۔", "85"),
    ],
)
def test_parses_urdu_and_arabic_indic_digits(response, expected):
    result = parse_answer(response)
    assert result.status == OK
    assert result.prediction == expected


@pytest.mark.parametrize(
    "response",
    [None, "", "   \n ", "The garden produced 768 vegetables.", "####", "#### \n", "#### about eighty", 42],
)
def test_missing_answers(response):
    result = parse_answer(response)
    assert result.status == MISSING
    assert result.value is None
    assert result.prediction is None


def test_final_answer_phrase_inside_reasoning_is_not_a_marker():
    result = parse_answer("To get the final answer we add 3 and 4 to make 7.")
    assert result.status == MISSING


@pytest.mark.parametrize(
    "response",
    [
        "#### 768 or 769",
        "#### 5-6",
        "#### 1,2",
        "#### 768\n\nQuestion: Tom has 3 bags of 4 apples.\n#### 12",
        "Final answer: 10\n#### 11",
    ],
)
def test_ambiguous_answers(response):
    result = parse_answer(response)
    assert result.status == AMBIGUOUS
    assert result.value is None


def test_repeated_same_number_after_marker_is_not_ambiguous():
    assert parse_answer("#### 1,200 (1200 dollars)").prediction == "1200"


def test_custom_marker_replaces_defaults():
    markers = (r"ANSWER\s*=",)
    assert parse_answer("ANSWER = 9", markers).prediction == "9"
    assert parse_answer("#### 9", markers).status == MISSING


@pytest.mark.parametrize(
    "response, expected",
    [
        ("Steps...\nFINAL_ANSWER 70", "70"),  # no colon (real Gemma 3 4B output)
        ("FINAL_ANSWER：70", "70"),  # full-width colon
        ("FINAL_ANSWER ۷۰", "70"),  # no colon, Urdu digits
        # Generic "final answer:" followed by a restated question, then the real marker (real 4B output):
        ("Here is the final answer:\n\nQuestion: Hans has 10 floors and 10 rooms.\n...\nFINAL_ANSWER: 90", "90"),
        ("FINAL_ANSWER: 3\nWait, recheck: 2 + 3 = 5.\nFINAL_ANSWER: 5", "5"),  # last FINAL_ANSWER wins
        # An echoed instruction after the answer is skipped, because no number follows it:
        ("FINAL_ANSWER: 70\nI used the literal marker FINAL_ANSWER: followed by the number.", "70"),
        ("Final answer: 12\n#### 12\nFINAL_ANSWER: 12", "12"),  # all agree: unchanged
    ],
)
def test_last_final_answer_marker_takes_priority(response, expected):
    result = parse_answer(response)
    assert result.status == OK
    assert result.prediction == expected


@pytest.mark.parametrize(
    "response, expected",
    [
        ("Final Answer: The final answer is 70.", "70"),  # no FINAL_ANSWER: earlier rule (real 1B output)
        ("**Final Answer:**\n\n70", "70"),  # blank lines after a generic marker are skipped, as before
        ("70 FINAL_ANSWER\nFinal answer: 70", "70"),  # FINAL_ANSWER without a number: fall back
    ],
)
def test_fallback_to_earlier_rule_without_a_usable_final_answer(response, expected):
    assert parse_answer(response).prediction == expected


def test_last_final_answer_with_several_numbers_is_ambiguous():
    result = parse_answer("FINAL_ANSWER: 5 or 6")
    assert result.status == AMBIGUOUS


def test_final_answer_priority_is_off_for_custom_markers():
    markers = (r"ANSWER\s*=",)
    assert parse_answer("ANSWER = 9\nFINAL_ANSWER: 4", markers).prediction == "9"


def test_find_numbers_keeps_negative_only_at_word_start():
    assert find_numbers("5-6 and -7") == [Decimal(5), Decimal(6), Decimal(-7)]


@pytest.mark.parametrize("raw, expected", [(768, "768"), ("1,200", "1200"), ("-15", "-15"), (2.5, "2.5"), ("۸۵", "85")])
def test_to_decimal_accepts_gold_formats(raw, expected):
    assert to_decimal(raw) == Decimal(expected)


@pytest.mark.parametrize("raw", [True, None, "", "5 or 6", [5]])
def test_to_decimal_rejects_unclear_gold(raw):
    with pytest.raises(ValueError):
        to_decimal(raw)


def test_equivalent_formats_are_correct():
    gold = Decimal(1200)
    for response in ("#### 1200", "#### 1,200", "#### 1200.00", "#### ١٢٠٠", "#### ۱۲۰۰"):
        parsed = parse_answer(response)
        assert is_correct(parsed.status, parsed.value, gold), response


def test_wrong_answer_is_incorrect():
    parsed = parse_answer("#### 767")
    assert parsed.status == OK
    assert not is_correct(parsed.status, parsed.value, Decimal(768))


def test_negative_sign_matters():
    parsed = parse_answer("#### 15")
    assert not is_correct(parsed.status, parsed.value, Decimal(-15))


@pytest.mark.parametrize("status", [MISSING, AMBIGUOUS])
def test_parse_failures_are_never_correct(status):
    assert not is_correct(status, Decimal(768), Decimal(768))


def test_score_record_appends_contract_fields_without_losing_raw_fields():
    raw = {"question_id": "q", "condition": "U-U-U", "strategy": "random", "raw_response": "#### ۷۶۸", "prompt": "p"}
    scored = score_record(raw, Decimal(768))
    assert scored["prompt"] == "p"
    assert scored["prediction"] == "768"
    assert scored["gold_answer"] == "768"
    assert scored["correct"] is True
    assert scored["parse_status"] == OK
    assert "prediction" not in raw


def test_gold_answers_reads_both_field_names():
    gold = gold_answers([{"id": "a", "answer_number": 768}, {"id": "b", "answer": "1,200"}])
    assert gold == {"a": Decimal(768), "b": Decimal(1200)}


def test_gold_answers_rejects_duplicates_and_missing_keys():
    with pytest.raises(ValueError):
        gold_answers([{"id": "a", "answer": "1"}, {"id": "a", "answer": "2"}])
    with pytest.raises(ValueError):
        gold_answers([{"id": "a"}])


def test_summarize_counts_parse_failures_in_denominator():
    records = [
        {"strategy": "random", "condition": "U-U-U", "shot_count": 2, "correct": True, "parse_status": OK},
        {"strategy": "random", "condition": "U-U-U", "shot_count": 2, "correct": False, "parse_status": OK},
        {"strategy": "random", "condition": "U-U-U", "shot_count": 2, "correct": False, "parse_status": MISSING},
        {"strategy": "random", "condition": "U-U-U", "shot_count": 2, "correct": False, "parse_status": AMBIGUOUS},
    ]
    [row] = summarize(records, ("strategy", "condition", "shot_count"))
    assert (row["correct"], row["total"], row["accuracy"]) == (1, 4, 0.25)
    assert (row["parse_failures"], row["missing"], row["ambiguous"]) == (2, 1, 1)


def test_contract_problems_flags_missing_fields_and_bad_demo_ids():
    good = {"question_id": "q", "condition": "U-U-U", "strategy": "random", "shot_count": 2, "seed": 1,
            "model_id": "m", "demo_ids": ["a", "b"], "prompt": "p", "raw_response": "r"}
    assert contract_problems(good, CONDITIONS) == []
    assert "missing prompt" in contract_problems({k: v for k, v in good.items() if k != "prompt"}, CONDITIONS)
    assert "repeated demo id" in contract_problems({**good, "demo_ids": ["a", "a"]}, CONDITIONS)
    assert "1 demo ids for shot_count 2" in contract_problems({**good, "demo_ids": ["a"]}, CONDITIONS)
    assert "unknown condition 'X-X-X'" in contract_problems({**good, "condition": "X-X-X"}, CONDITIONS)


def test_reconcile_keeps_last_successful_duplicate():
    base = {"question_id": "q", "condition": "U-U-U", "strategy": "random", "shot_count": 2, "seed": 1,
            "model_id": "m", "demo_ids": ["a", "b"], "prompt": "p"}
    records = [{**base, "raw_response": "#### 1"}, {**base, "raw_response": "#### 2"}]
    kept, summary = reconcile(records, {"q": Decimal(2)}, conditions=("U-U-U",), strategies=("random",))
    assert [r["raw_response"] for r in kept] == ["#### 2"]
    assert summary["duplicates_dropped"] == 1
    assert summary["conflicting_duplicates"] == 1


EXPECTED_CELLS = {
    ("random", "U-U-U"): (3, 3, 0, 0),
    ("random", "U-U-E"): (3, 3, 0, 0),
    ("random", "U-E-E"): (1, 3, 0, 0),
    ("random", "E-E-E"): (2, 3, 0, 0),
    ("similarity", "U-U-U"): (2, 3, 1, 0),
    ("similarity", "U-U-E"): (1, 2, 1, 0),
    ("similarity", "U-E-E"): (1, 3, 0, 1),
    ("similarity", "E-E-E"): (2, 3, 0, 1),
}


@pytest.fixture
def fixture_report(tmp_path):
    return build_report(RAW_FIXTURE, DEV_FIXTURE, tmp_path, prefix="fixture")


def test_fixture_grades_every_cell_correctly(fixture_report):
    rows = fixture_report["rows"]
    cells = {(r["strategy"], r["condition"]): r for r in rows if "ALL" not in (r["strategy"], r["condition"])}
    assert set(cells) == set(EXPECTED_CELLS)
    for key, (correct, total, missing, ambiguous) in EXPECTED_CELLS.items():
        row = cells[key]
        assert (row["correct"], row["total"], row["missing"], row["ambiguous"]) == (correct, total, missing, ambiguous), key


def test_fixture_margins(fixture_report):
    margins = {(r["strategy"], r["condition"]): r for r in fixture_report["rows"]}
    assert (margins[("random", "ALL")]["correct"], margins[("random", "ALL")]["total"]) == (9, 12)
    assert (margins[("similarity", "ALL")]["correct"], margins[("similarity", "ALL")]["total"]) == (6, 11)
    overall = margins[("ALL", "ALL")]
    assert (overall["correct"], overall["total"], overall["parse_failures"]) == (15, 23, 4)
    assert overall["accuracy"] == round(15 / 23, 4)


def test_fixture_reconciliation_accounts_for_every_raw_line(fixture_report):
    rec = fixture_report["reconciliation"]
    assert rec["raw_records"] == 27
    assert rec["malformed_raw_lines"] == [28]
    assert rec["failed_calls"] == 2
    assert rec["duplicates_dropped"] == 1
    assert rec["conflicting_duplicates"] == 0
    assert rec["unknown_question_ids"] == ["gsm8k-train-000000000000"]
    assert rec["unique_successful_scored"] == 23
    assert rec["expected_configurations"] == 24
    assert rec["missing_configurations"] == [
        {"question_id": "synthetic-negative-01", "condition": "U-U-E", "strategy": "similarity", "shot_count": 2, "seed": 42}
    ]
    assert rec["totals_balance"] is True
    assert rec["complete"] is False


def test_fixture_outputs_are_written_separately(fixture_report, tmp_path):
    paths = fixture_report["paths"]
    evaluated = [json.loads(line) for line in paths["evaluated"].read_text(encoding="utf-8").splitlines()]
    assert len(evaluated) == 23
    for record in evaluated:
        assert {"prediction", "gold_answer", "correct", "parse_status", "raw_response", "prompt"} <= record.keys()
    with open(paths["summary_csv"], encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0].keys() >= {"strategy", "condition", "correct", "total", "accuracy", "parse_failures"}
    assert "| random | U-U-U | 2 | 3 / 3 | 100.0% |" in paths["summary_md"].read_text(encoding="utf-8")
    assert not any(p.resolve() == RAW_FIXTURE.resolve() for p in paths.values())


def test_complete_run_passes_reconciliation(tmp_path):
    dev = tmp_path / "dev.jsonl"
    dev.write_text(json.dumps({"id": "q1", "answer_number": 768}) + "\n", encoding="utf-8")
    lines = []
    for strategy in ("random", "similarity"):
        for condition in CONDITIONS:
            lines.append(json.dumps({
                "question_id": "q1", "condition": condition, "strategy": strategy, "shot_count": 2, "seed": 7,
                "model_id": "m", "demo_ids": ["a", "b"], "prompt": "p", "raw_response": "#### 768",
            }))
    raw = tmp_path / "raw.jsonl"
    raw.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = build_report(raw, dev, tmp_path / "out")
    assert result["reconciliation"]["complete"] is True
    assert result["reconciliation"]["unique_successful_scored"] == 8
    assert main(["--allow-fixtures", "--raw", str(raw), "--dev", str(dev), "--out-dir", str(tmp_path / "cli")]) == 0


def test_cli_flags_incomplete_runs(tmp_path):
    assert main(["--allow-fixtures", "--raw", str(RAW_FIXTURE), "--dev", str(DEV_FIXTURE), "--out-dir", str(tmp_path)]) == 1


def test_refuses_to_overwrite_raw_file(tmp_path):
    raw = tmp_path / "pilot_evaluated.jsonl"
    raw.write_text(RAW_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError):
        build_report(raw, DEV_FIXTURE, tmp_path)


def test_full_summary_has_cell_and_margin_rows(fixture_report):
    rows = fixture_report["rows"]
    assert len([r for r in rows if "ALL" not in (r["strategy"], r["condition"])]) == 8
    assert len(rows) == 8 + 2 + 4 + 1
    assert rows == full_summary(json.loads(line) for line in fixture_report["paths"]["evaluated"].read_text(encoding="utf-8").splitlines())
