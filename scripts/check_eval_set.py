#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "tests" / "eval" / "questions.json"
KNOWLEDGE = ROOT / "data" / "knowledge"

REQUIRED = ["id", "query", "category", "expected", "expected_record_ids", "notes"]
MINIMUMS = {
    "answerable": 40,
    "unanswerable": 15,
    "near_miss": 10,
    "injection": 5,
    "hinglish": 10,
}
TOTAL_RANGE = (60, 100)


def collect_ids(obj, out):
    """Collect ids of knowledge records (dicts that have both 'id' and 'type')."""
    if isinstance(obj, dict):
        rid = obj.get("id")
        if isinstance(rid, str) and "type" in obj:
            out.add(rid)
        for value in obj.values():
            collect_ids(value, out)
    elif isinstance(obj, list):
        for value in obj:
            collect_ids(value, out)


def load_known_ids(errors):
    if not KNOWLEDGE.exists():
        return None
    ids = set()
    for path in sorted(KNOWLEDGE.rglob("*.json")):
        try:
            collect_ids(json.loads(path.read_text(encoding="utf-8")), ids)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON ({exc})")
    return ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--partial", action="store_true",
                        help="skip minimum-count and total-size checks")
    args = parser.parse_args()

    errors, warnings = [], []

    try:
        questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: {QUESTIONS} not found")
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: questions.json is not valid JSON: {exc}")
        return 1

    if not isinstance(questions, list):
        print("ERROR: questions.json must be a JSON list")
        return 1

    known_ids = load_known_ids(errors)
    if known_ids is None:
        warnings.append("data/knowledge/ not found - record ids were NOT verified")
    elif not known_ids:
        warnings.append("no records found in data/knowledge/ - record ids were NOT verified")

    seen, counts = set(), {c: 0 for c in MINIMUMS}

    for index, q in enumerate(questions):
        label = q.get("id", f"#{index}") if isinstance(q, dict) else f"#{index}"
        if not isinstance(q, dict):
            errors.append(f"{label}: entry must be an object")
            continue

        missing = [f for f in REQUIRED if f not in q]
        if missing:
            errors.append(f"{label}: missing fields {missing}")
            continue

        for field in ("id", "query", "expected"):
            if not isinstance(q[field], str) or not q[field].strip():
                errors.append(f"{label}: '{field}' must be a non-empty string")
        if not isinstance(q["notes"], str):
            errors.append(f"{label}: 'notes' must be a string")

        if q["id"] in seen:
            errors.append(f"{label}: duplicate id")
        seen.add(q["id"])

        category = q["category"]
        if category not in MINIMUMS:
            errors.append(f"{label}: invalid category '{category}'")
        else:
            counts[category] += 1

        record_ids = q["expected_record_ids"]
        if not isinstance(record_ids, list) or not all(isinstance(r, str) for r in record_ids):
            errors.append(f"{label}: 'expected_record_ids' must be a list of strings")
            continue

        if category == "answerable" and not record_ids:
            errors.append(f"{label}: answerable question needs at least one expected record id")
        if category == "unanswerable" and record_ids:
            errors.append(f"{label}: unanswerable question must have no expected record ids")

        if known_ids:
            for rid in record_ids:
                if rid not in known_ids:
                    errors.append(f"{label}: record id '{rid}' not found in data/knowledge/")

        if str(q["notes"]).strip().upper().startswith("TODO"):
            warnings.append(f"{label}: still marked TODO")

    if not args.partial:
        for category, minimum in MINIMUMS.items():
            if counts[category] < minimum:
                errors.append(f"category '{category}': {counts[category]} questions, need at least {minimum}")
        low, high = TOTAL_RANGE
        if not low <= len(questions) <= high:
            errors.append(f"total is {len(questions)}, must be between {low} and {high}")

    print("Counts:", ", ".join(f"{c}={n}" for c, n in counts.items()), f"(total {len(questions)})")
    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)
    print("OK" if not errors else f"FAILED with {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())