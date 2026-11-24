from decimal import Decimal

from .answer_parser import AMBIGUOUS, DEFAULT_MARKERS, MISSING, OK, format_decimal, parse_answer, to_decimal

CONDITIONS = ("U-U-U", "U-U-E", "U-E-E", "E-E-E")
STRATEGIES = ("random", "similarity")
ALL = "ALL"

GROUPINGS = (
    ("strategy", "condition", "shot_count"),
    ("strategy", "shot_count"),
    ("condition", "shot_count"),
    ("shot_count",),
)

SUMMARY_FIELDS = (
    "strategy",
    "condition",
    "shot_count",
    "correct",
    "total",
    "accuracy",
    "parse_failures",
    "missing",
    "ambiguous",
)


def gold_answers(dev_records) -> dict:
    gold = {}
    for record in dev_records:
        key = "answer_number" if "answer_number" in record else "answer"
        if key not in record:
            raise ValueError(f"dev record {record.get('id')!r} has no answer_number/answer")
        if record["id"] in gold:
            raise ValueError(f"duplicate dev id {record['id']!r}")
        gold[record["id"]] = to_decimal(record[key])
    return gold


def is_correct(parse_status: str, prediction, gold: Decimal) -> bool:
    if parse_status != OK:
        return False
    if prediction is None:
        return False
    return to_decimal(prediction) == gold


def score_record(record: dict, gold: Decimal, markers=DEFAULT_MARKERS) -> dict:
    parsed = parse_answer(record.get("raw_response"), markers)
    scored = dict(record)
    scored["prediction"] = parsed.prediction
    scored["gold_answer"] = format_decimal(gold)
    scored["correct"] = is_correct(parsed.status, parsed.value, gold)
    scored["parse_status"] = parsed.status
    scored["parse_detail"] = parsed.detail
    return scored


def _empty_counts() -> dict:
    return {"correct": 0, "total": 0, "missing": 0, "ambiguous": 0}


def _accuracy(correct: int, total: int):
    if total == 0:
        return None
    return round(correct / total, 4)


def _sort_key(group: dict):
    def position(value, order):
        if value == ALL:
            return (2, "")
        if value in order:
            return (0, order.index(value))
        return (1, str(value))

    return (
        position(group["strategy"], STRATEGIES),
        position(group["condition"], CONDITIONS),
        str(group["shot_count"]),
    )


def summarize(scored_records, group_keys) -> list:
    buckets = {}
    for record in scored_records:
        label = tuple(record[key] for key in group_keys)
        counts = buckets.setdefault(label, _empty_counts())
        counts["total"] += 1
        counts["correct"] += int(record["correct"])
        if record["parse_status"] == MISSING:
            counts["missing"] += 1
        if record["parse_status"] == AMBIGUOUS:
            counts["ambiguous"] += 1

    rows = []
    for label, counts in buckets.items():
        row = {"strategy": ALL, "condition": ALL, "shot_count": ALL}
        row.update(zip(group_keys, label))
        row["correct"] = counts["correct"]
        row["total"] = counts["total"]
        row["accuracy"] = _accuracy(counts["correct"], counts["total"])
        row["missing"] = counts["missing"]
        row["ambiguous"] = counts["ambiguous"]
        row["parse_failures"] = counts["missing"] + counts["ambiguous"]
        rows.append({field: row[field] for field in SUMMARY_FIELDS})
    return sorted(rows, key=_sort_key)


def full_summary(scored_records) -> list:
    scored_records = list(scored_records)
    rows = []
    for keys in GROUPINGS:
        rows.extend(summarize(scored_records, keys))
    return rows
