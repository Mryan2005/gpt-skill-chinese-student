"""Run the Card Atomicity and Card Size gates for a study-math record.

The structural parser lives in validate_math.py.  This thin boundary tool
keeps card-focused CI and authoring feedback short while reusing the same
source of truth for IDs, types, and references.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_math import CARD_TYPES, Issue, validate_record


CARD_ISSUES = {
    "CARD_NOT_ATOMIC",
    "CARD_TOO_BROAD",
    "CARD_TOO_LARGE",
    "DOMAIN_TEMPLATE_MISMATCH",
    "EMPTY_BRIDGE",
    "QUESTION_CARD_MISMATCH",
}


def validate_cards(record: object, required_types: set[str] | None = None) -> tuple[bool, dict[str, object]]:
    report = validate_record(record)
    record_dict = record if isinstance(record, dict) else {}
    cards = record_dict.get("cards", []) if isinstance(record_dict, dict) else []
    card_types = {
        card.get("type")
        for card in cards
        if isinstance(card, dict) and isinstance(card.get("type"), str)
    }
    missing_types = sorted((required_types or set()) - card_types)
    issues = [issue for issue in report.issues if issue.code in CARD_ISSUES]
    for card_type in missing_types:
        issues.append(Issue("CARD_TYPE_MISSING", "cards", f"required card type is missing: {card_type}"))
    payload = {
        "passed": not issues,
        "cardGate": "PASS" if not issues else "FAIL",
        "cardTypes": sorted(card_types & CARD_TYPES),
        "missingRequiredTypes": missing_types,
        "issues": [
            {"code": issue.code, "path": issue.path, "message": issue.message}
            for issue in issues
        ],
        "metrics": {
            "atomic_card_rate": report.metrics.get("atomic_card_rate", 0),
            "card_size_violation_rate": report.metrics.get("card_size_violation_rate", 0),
        },
    }
    return not issues, payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate study-math card atomicity and size.")
    parser.add_argument("record", type=Path, help="Structured math record JSON file")
    parser.add_argument("--require-type", action="append", default=[], choices=sorted(CARD_TYPES))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    passed, payload = validate_cards(record, set(args.require_type))
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"CARD_GATE: {payload['cardGate']}")
        print(f"CARD_TYPES: {', '.join(payload['cardTypes']) or 'none'}")
        for issue in payload["issues"]:
            print(f"- [{issue['code']}] {issue['path']}: {issue['message']}")
        for key, value in payload["metrics"].items():
            print(f"- {key}: {value}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
