"""Validate the read-only structured finding report produced by check."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SEVERITIES = {"blocker", "error", "warning", "info"}
REQUIRED_FINDING_FIELDS = {
    "id",
    "code",
    "severity",
    "subject",
    "entityType",
    "entityId",
    "observed",
    "expected",
    "evidence",
    "layer",
    "repairOwner",
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _evidence(value: Any) -> bool:
    if _text(value):
        return True
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(item, dict) and any(_text(part) for part in item.values()) for item in value)


def validate_report(report: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report must be an object"]
    if report.get("schemaVersion") != "check.finding.v1":
        errors.append("schemaVersion must be check.finding.v1")
    if report.get("readOnly") is not True:
        errors.append("readOnly must be true")
    findings = report.get("findings")
    if not isinstance(findings, list):
        return errors + ["findings must be a list"]
    summary = report.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object")
        summary = {}
    seen_ids: set[str] = set()
    actual: Counter[str] = Counter()
    for index, finding in enumerate(findings):
        path = f"findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{path} must be an object")
            continue
        missing = sorted(REQUIRED_FINDING_FIELDS - set(finding))
        if missing:
            errors.append(f"{path} missing fields: {', '.join(missing)}")
        finding_id = finding.get("id")
        if not _text(finding_id):
            errors.append(f"{path}.id must be non-empty")
        elif finding_id in seen_ids:
            errors.append(f"{path}.id is duplicated: {finding_id}")
        else:
            seen_ids.add(finding_id)
        severity = finding.get("severity")
        if severity not in SEVERITIES:
            errors.append(f"{path}.severity is invalid: {severity}")
        else:
            actual[severity] += 1
        for field in ("code", "subject", "entityType", "entityId", "observed", "expected", "layer", "repairOwner"):
            if not _text(finding.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if not _evidence(finding.get("evidence")):
            errors.append(f"{path}.evidence must contain a location or evidence object")
        if finding.get("status", "open") not in {"open", "noted", "verified"}:
            errors.append(f"{path}.status is invalid")
    for severity in SEVERITIES:
        declared = summary.get(severity, 0)
        if not isinstance(declared, int) or declared < 0:
            errors.append(f"summary.{severity} must be a non-negative integer")
        elif declared != actual[severity]:
            errors.append(f"summary.{severity}={declared} does not match findings ({actual[severity]})")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a check finding report.")
    parser.add_argument("report", type=Path)
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_report(report)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated {len(report['findings'])} finding(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
