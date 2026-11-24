#!/usr/bin/env python3
"""Load and validate paired GSM8K demo/development JSONL files (stdlib only)."""
import argparse
import ast
import hashlib
import json
import re
import sys
import unicodedata
from decimal import Decimal
from pathlib import Path

REQUIRED = {"id", "split", "source", "source_revision", "question_en", "question_ur", "answer_number", "answer_unit", "calculations", "solution_en", "solution_ur", "translation_status", "reviewer", "review_date", "uncertainties"}
NUM = re.compile(r"(?<![\w.])[-+]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)(?!\w)")
FINAL = re.compile(r"####\s*([-+]?\d+(?:\.\d+)?)\s*$")

def decimal(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a number")
    return Decimal(str(value).replace(",", ""))

def evaluate(expression):
    def walk(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return decimal(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -walk(node.operand)
        if isinstance(node, ast.BinOp):
            a, b = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
        raise ValueError("Unsupported expression")
    return walk(ast.parse(expression, mode="eval").body)

def load(path):
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8", errors="strict")
    rows = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            raise ValueError(f"{path}:{line_no}: blank line")
        rows.append(json.loads(line))
    return rows

def validate(paths, expected_counts=None, require_human=False, source_train=None, mgsm_en=None):
    errors, rows, seen = [], [], set()
    for path in paths:
        try:
            part = load(path)
        except Exception as exc:
            errors.append(f"{path}: {exc}")
            continue
        if expected_counts and Path(path).name in expected_counts and len(part) != expected_counts[Path(path).name]:
            errors.append(f"{path}: expected {expected_counts[Path(path).name]} records; found {len(part)}")
        rows.extend(part)
    by_split = {"demo": set(), "dev": set()}
    for i, row in enumerate(rows, 1):
        label = f"record {i} ({row.get('id', '?')})"
        absent = REQUIRED - row.keys()
        if absent:
            errors.append(f"{label}: missing {sorted(absent)}")
            continue
        rid = row["id"]
        if not isinstance(rid, str) or not re.fullmatch(r"gsm8k-train-[0-9a-f]{12}", rid):
            errors.append(f"{label}: invalid synthetic ID")
        elif isinstance(row["question_en"], str):
            expected_id = "gsm8k-train-" + hashlib.sha256(row["question_en"].encode("utf-8")).hexdigest()[:12]
            if rid != expected_id: errors.append(f"{label}: ID does not match English question")
        if rid in seen: errors.append(f"{label}: duplicate ID")
        seen.add(rid)
        split = row["split"]
        if split not in by_split: errors.append(f"{label}: invalid split")
        else: by_split[split].add(rid)
        if row["source"] != "gsm8k/main/train": errors.append(f"{label}: source is not GSM8K train")
        if row["source_revision"] != "3101c7d5072418e28b9008a6636bde82a006892c":
            errors.append(f"{label}: unexpected source revision")
        for key in ("question_en", "question_ur", "solution_en", "solution_ur", "answer_unit"):
            value = row[key]
            if not isinstance(value, str) or not value.strip(): errors.append(f"{label}: empty {key}")
            elif value != unicodedata.normalize("NFC", value): errors.append(f"{label}: non-NFC {key}")
        if not re.search(r"[\u0600-\u06ff]", row["question_ur"]): errors.append(f"{label}: Urdu script absent")
        if not isinstance(row["uncertainties"], list): errors.append(f"{label}: uncertainties must be a list")
        status = row["translation_status"]
        if status not in ("draft", "verified"): errors.append(f"{label}: invalid translation status")
        if status == "verified" and (not row["reviewer"] or not row["review_date"]):
            errors.append(f"{label}: verified needs human reviewer and date")
        if require_human and status != "verified": errors.append(f"{label}: human review pending")
        try:
            expected = decimal(row["answer_number"])
            calculations = row["calculations"]
            if not isinstance(calculations, list) or not calculations: raise ValueError("no calculations")
            for step in calculations:
                actual = evaluate(step["expression"])
                if actual != decimal(step["result"]): raise ValueError(f"{step['expression']} = {actual}, not {step['result']}")
                if not step.get("unit"): raise ValueError("step unit missing")
            if decimal(calculations[-1]["result"]) != expected: raise ValueError("last calculation differs from answer")
            if calculations[-1]["unit"] != row["answer_unit"]: raise ValueError("final unit differs from answer_unit")
            for lang in ("en", "ur"):
                match = FINAL.search(row[f"solution_{lang}"])
                if not match or decimal(match.group(1)) != expected: raise ValueError(f"{lang} final answer mismatch")
            en_nums = sorted(set(decimal(x.group()) for x in NUM.finditer(row["question_en"])))
            ur_nums = sorted(set(decimal(x.group()) for x in NUM.finditer(row["question_ur"])))
            if en_nums != ur_nums: raise ValueError(f"digit mismatch EN={en_nums}, UR={ur_nums}")
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    if by_split["demo"] & by_split["dev"]: errors.append("demo/dev IDs overlap")
    if source_train:
        try:
            original = {r["question"]: r for r in load(source_train)}
            for row in rows:
                item = original.get(row["question_en"])
                if item is None:
                    errors.append(f"{row['id']}: question absent from supplied GSM8K train file")
                else:
                    final = item["answer"].rsplit("####", 1)[-1].strip()
                    if decimal(final) != decimal(row["answer_number"]):
                        errors.append(f"{row['id']}: GSM8K source answer mismatch")
        except Exception as exc:
            errors.append(f"source train: {exc}")
    if mgsm_en:
        try:
            mgsm_questions = {line.split("\t", 1)[0] for line in Path(mgsm_en).read_text(encoding="utf-8").splitlines()}
            for row in rows:
                if row["question_en"] in mgsm_questions:
                    errors.append(f"{row['id']}: overlaps MGSM evaluation question")
        except Exception as exc:
            errors.append(f"MGSM English: {exc}")
    return rows, errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--require-human", action="store_true")
    ap.add_argument("--full", action="store_true", help="Require 20 demo and 10 dev records")
    ap.add_argument("--source-train", type=Path, help="Optional original GSM8K train.jsonl to verify exact questions and answer keys")
    ap.add_argument("--mgsm-en", type=Path, help="Optional original mgsm_en.tsv to test evaluation overlap")
    args = ap.parse_args()
    counts = {"demo.jsonl": 20, "dev.jsonl": 10} if args.full else None
    rows, errors = validate(args.files, counts, args.require_human, args.source_train, args.mgsm_en)
    print(json.dumps({"records": len(rows), "demo": sum(r.get("split") == "demo" for r in rows), "dev": sum(r.get("split") == "dev" for r in rows), "human_verified": sum(r.get("translation_status") == "verified" for r in rows), "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__": sys.exit(main())
