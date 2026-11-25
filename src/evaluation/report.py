import argparse
import hashlib
import csv
import itertools
import json
import sys
from pathlib import Path

from .answer_parser import DEFAULT_MARKERS, PARSER_VERSION
from .metrics import ALL, CONDITIONS, STRATEGIES, SUMMARY_FIELDS, full_summary, gold_answers, score_record

RAW_FIELDS = (
    "question_id",
    "condition",
    "strategy",
    "shot_count",
    "seed",
    "model_id",
    "demo_ids",
    "prompt",
    "raw_response",
)
KEY_FIELDS = ("question_id", "condition", "strategy", "shot_count", "seed")


def read_jsonl(path):
    records, malformed = [], []
    with open(path, encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                malformed.append(line_no)
                continue
            if not isinstance(parsed, dict):
                malformed.append(line_no)
                continue
            records.append(parsed)
    return records, malformed


def contract_problems(record: dict, conditions) -> list:
    problems = [f"missing {field}" for field in RAW_FIELDS if field not in record]
    if record.get("condition") not in conditions:
        problems.append(f"unknown condition {record.get('condition')!r}")
    demo_ids = record.get("demo_ids")
    if not isinstance(demo_ids, list):
        problems.append("demo_ids is not a list")
        return problems
    if len(set(demo_ids)) != len(demo_ids):
        problems.append("repeated demo id")
    if isinstance(record.get("shot_count"), int) and len(demo_ids) != record["shot_count"]:
        problems.append(f"{len(demo_ids)} demo ids for shot_count {record['shot_count']}")
    return problems


def is_successful(record: dict) -> bool:
    if record.get("error") or record.get("status", "success") != "success":
        return False
    response = record.get("raw_response")
    return isinstance(response, str) and bool(response.strip())


def record_key(record: dict):
    if any(record.get(field) is None for field in KEY_FIELDS):
        return None
    return tuple(record[field] for field in KEY_FIELDS)


def _describe(key) -> dict:
    return dict(zip(KEY_FIELDS, key))


def _deduplicate(records):
    kept, unusable, failed, dropped, conflicts = {}, 0, 0, 0, 0
    for record in records:
        key = record_key(record)
        if key is None:
            unusable += 1
            continue
        if not is_successful(record):
            failed += 1
            continue
        if key in kept:
            dropped += 1
            if kept[key]["raw_response"] != record["raw_response"]:
                conflicts += 1
        kept[key] = record
    return kept, unusable, failed, dropped, conflicts


def reconcile(records, gold, conditions=CONDITIONS, strategies=STRATEGIES, shots=(2,), expected_seeds=None):
    kept, unusable, failed, dropped, conflicts = _deduplicate(records)

    scorable = {key: rec for key, rec in kept.items() if key[0] in gold}
    unknown = sorted(key[0] for key in kept if key[0] not in gold)

    seeds = list(expected_seeds) if expected_seeds is not None else sorted({rec["seed"] for rec in records if rec.get("seed") is not None}, key=str)
    expected = set(itertools.product(sorted(gold), conditions, strategies, shots, seeds))
    missing = sorted(expected - scorable.keys(), key=str)
    unexpected = sorted(scorable.keys() - expected, key=str)

    problems = []
    for record in scorable.values():
        found = contract_problems(record, conditions)
        if found:
            problems.append({"question_id": record["question_id"], "condition": record["condition"],
                             "strategy": record["strategy"], "problems": found})

    accounted = unusable + failed + dropped + len(unknown) + len(scorable)
    summary = {
        "raw_records": len(records),
        "unusable_records": unusable,
        "failed_calls": failed,
        "duplicates_dropped": dropped,
        "conflicting_duplicates": conflicts,
        "unknown_question_records": len(unknown),
        "unique_successful_scored": len(scorable),
        "expected_configurations": len(expected),
        "seeds_seen": seeds,
        "missing_configurations": [_describe(key) for key in missing],
        "unexpected_configurations": [_describe(key) for key in unexpected],
        "unknown_question_ids": unknown,
        "contract_problems": problems,
        "totals_balance": accounted == len(records),
        "run_identities": sorted({str(rec.get("run_id")) for rec in records if rec.get("run_id") is not None}),
        "model_identities": sorted({str(rec.get("model_id")) for rec in records if rec.get("model_id") is not None}),
    }
    return list(scorable.values()), summary


def is_complete(summary: dict, malformed_lines) -> bool:
    return (
        summary["totals_balance"]
        and summary["expected_configurations"] > 0
        and not summary["unusable_records"]
        and not summary["unknown_question_records"]
        and not summary["conflicting_duplicates"]
        and not summary["unexpected_configurations"]
        and len(summary["run_identities"]) <= 1
        and len(summary["model_identities"]) <= 1
        and not malformed_lines
        and not summary["missing_configurations"]
        and not summary["contract_problems"]
        and summary["unique_successful_scored"] == summary["expected_configurations"]
    )


def _percent(value) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def markdown_table(rows) -> str:
    lines = [
        "| Strategy | Condition | Shots | Correct / total | Accuracy | Parse failures (missing / ambiguous) |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['strategy']} | {row['condition']} | {row['shot_count']} | "
            f"{row['correct']} / {row['total']} | {_percent(row['accuracy'])} | "
            f"{row['parse_failures']} ({row['missing']} / {row['ambiguous']}) |"
        )
    return "\n".join(lines)


def write_jsonl(path: Path, records) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ("" if v is None else v) for k, v in row.items()})


def _sorted_scored(scored):
    return sorted(scored, key=lambda r: tuple(str(r[f]) for f in KEY_FIELDS))


def build_report(raw_path, dev_path, out_dir, prefix="pilot", conditions=CONDITIONS,
                 strategies=STRATEGIES, shots=(2,), markers=DEFAULT_MARKERS, manifest_path=None) -> dict:
    raw_path, out_dir = Path(raw_path), Path(out_dir)
    records, malformed = read_jsonl(raw_path)
    dev_records, dev_malformed = read_jsonl(dev_path)
    if dev_malformed:
        raise ValueError(f"{dev_path}: malformed lines {dev_malformed}")
    gold = gold_answers(dev_records)

    manifest = None
    if manifest_path is not None:
        manifest = json.loads(Path(manifest_path).read_text())
        config = manifest["identity"]["configuration"]
        if manifest.get("mode") != "live" or config.get("data_kind") != "real" or config["model"]["backend"] == "mock":
            raise ValueError("Research evaluation requires a live, real-data manifest")
        dev_hash = hashlib.sha256(Path(dev_path).read_bytes()).hexdigest()
        if manifest["identity"]["data"]["dev_path"] != dev_hash:
            raise ValueError("Development answers do not match the inference manifest")
        conditions, strategies, shots = tuple(config["conditions"]), tuple(config["strategies"]), (config["shot_count"],)
        planned = {p["record_id"]: p for p in manifest["plan"]}
        if len(planned) != manifest["expected_records"] or not planned:
            raise ValueError("Invalid or empty frozen experiment plan")
        seen = {}
        for record in records:
            plan = planned.get(record.get("record_id"))
            if plan is None or record.get("run_id") != manifest["run_id"]:
                raise ValueError("Raw record is outside this frozen run")
            if record.get("mode") != "live" or record.get("data_kind") != "real":
                raise ValueError("Mock or synthetic records cannot enter research evaluation")
            if record.get("model_id") != config["model"]["model_id"]:
                raise ValueError("Mixed model identities")
            for key in ("question_id", "condition", "strategy", "shot_count", "seed", "demo_ids", "prompt", "prompt_hash"):
                if record.get(key) != plan[key]:
                    raise ValueError("Raw record differs from the frozen prompt plan")
            if record.get("data_fingerprints") != manifest["identity"]["data"] or record.get("inference_settings") != config["model"]:
                raise ValueError("Raw provenance differs from the frozen run")
            if is_successful(record):
                if record["record_id"] in seen:
                    raise ValueError("Duplicate successful record in the real run")
                seen[record["record_id"]] = record["raw_response"]
    elif any(r.get("mode") == "live" or r.get("data_kind") == "real" for r in records):
        raise ValueError("Real inference needs its matching manifest")

    usable, reconciliation = reconcile(records, gold, conditions, strategies, shots,
                                       (config["seed"],) if manifest is not None else None)
    reconciliation["research_eligible"] = manifest is not None
    reconciliation["evaluation_kind"] = "real_pilot" if manifest is not None else "fixture_engineering_check"
    reconciliation["raw_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    reconciliation["parser_version"] = PARSER_VERSION
    reconciliation["parser_sha256"] = hashlib.sha256(Path(__file__).with_name("answer_parser.py").read_bytes()).hexdigest()
    reconciliation["parser_markers"] = list(markers)
    if manifest is not None:
        reconciliation["manifest_sha256"] = hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()
        reconciliation["run_id"] = manifest["run_id"]
    reconciliation["malformed_raw_lines"] = malformed
    reconciliation["complete"] = is_complete(reconciliation, malformed)

    scored = _sorted_scored(score_record(rec, gold[rec["question_id"]], markers) for rec in usable)
    rows = full_summary(scored)

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "evaluated": out_dir / f"{prefix}_evaluated.jsonl",
        "summary_csv": out_dir / f"{prefix}_summary.csv",
        "summary_md": out_dir / f"{prefix}_summary.md",
        "reconciliation": out_dir / f"{prefix}_reconciliation.json",
    }
    if raw_path.resolve() in {p.resolve() for p in paths.values()}:
        raise ValueError("refusing to overwrite the raw inference file")

    main_rows = [r for r in rows if ALL not in (r["strategy"], r["condition"])]
    margin_rows = [r for r in rows if r not in main_rows]
    table = markdown_table(main_rows) + "\n\nMargins\n\n" + markdown_table(margin_rows) + "\n"

    write_jsonl(paths["evaluated"], scored)
    reconciliation["evaluated_sha256"] = hashlib.sha256(paths["evaluated"].read_bytes()).hexdigest()
    write_csv(paths["summary_csv"], rows)
    paths["summary_md"].write_text(table, encoding="utf-8")
    paths["reconciliation"].write_text(json.dumps(reconciliation, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"rows": rows, "reconciliation": reconciliation, "paths": paths, "table": table}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Score raw inference JSONL and write the pilot summary.")
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--dev", required=True, type=Path)
    parser.add_argument("--out-dir", default=Path("results"), type=Path)
    parser.add_argument("--prefix", default="pilot")
    parser.add_argument("--manifest", type=Path, help="Matching raw inference manifest; required for research results")
    parser.add_argument("--allow-fixtures", action="store_true", help="Explicitly label non-research fixture checks")
    parser.add_argument("--conditions", nargs="+", default=list(CONDITIONS))
    parser.add_argument("--strategies", nargs="+", default=list(STRATEGIES))
    parser.add_argument("--shots", nargs="+", type=int, default=[2])
    parser.add_argument("--marker", action="append", dest="markers",
                        help="Regex for the final-answer marker; repeat to add more. Defaults to the built-in list.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    if args.manifest is None and not args.allow_fixtures:
        raise ValueError("Supply --manifest for research evaluation or --allow-fixtures for engineering checks")
    markers = tuple(args.markers) if args.markers else DEFAULT_MARKERS
    result = build_report(args.raw, args.dev, args.out_dir, args.prefix,
                          tuple(args.conditions), tuple(args.strategies), tuple(args.shots), markers, args.manifest)
    rec = result["reconciliation"]
    print(result["table"])
    print(f"raw={rec['raw_records']} scored={rec['unique_successful_scored']} "
          f"expected={rec['expected_configurations']} failed={rec['failed_calls']} "
          f"duplicates={rec['duplicates_dropped']} missing={len(rec['missing_configurations'])} "
          f"malformed={len(rec['malformed_raw_lines'])} balanced={rec['totals_balance']}")
    for name, path in result["paths"].items():
        print(f"{name}: {path}")
    if not rec["complete"]:
        print("INCOMPLETE: see the reconciliation file before using these numbers.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, TypeError, OSError):
        print("Invalid evaluation inputs or provenance; check the raw journal, manifest and dev file.", file=sys.stderr)
        sys.exit(2)
