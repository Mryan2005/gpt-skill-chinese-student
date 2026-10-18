"""Validate material-review output without attributing agent errors to users."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def validate_material_review(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["material review must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") != "material-review.report.v1":
        errors.append("schemaVersion must be material-review.report.v1")
    for field in ("reviewRunId", "examRunId", "subjectId"):
        if not isinstance(report.get(field), str) or not report[field].strip():
            errors.append(f"{field} must be non-empty")
    if report.get("answererType") not in {"human", "agent", "model", "unknown"}:
        errors.append("answererType is invalid")
    if report.get("answererType") != "human" and report.get("learnerModelWriteAllowed") is not False:
        errors.append("non-human material review cannot write Learner Model")
    if report.get("examResultMutation") is not False:
        errors.append("examResultMutation must be false")
    for field in ("counts", "blockers", "annotations", "studyGuideMarkdown", "routes"):
        if field not in report:
            errors.append(f"{field} is required")
    if not isinstance(report.get("blockers"), list):
        errors.append("blockers must be a list")
    if not isinstance(report.get("annotations"), list):
        errors.append("annotations must be a list")
    else:
        for index, annotation in enumerate(report["annotations"]):
            path = f"annotations[{index}]"
            if not isinstance(annotation, dict):
                errors.append(f"{path} must be an object")
                continue
            if not annotation.get("evidenceRefs"):
                errors.append(f"{path}.evidenceRefs must be non-empty")
            if annotation.get("targetType") == "card" and not annotation.get("targetId"):
                errors.append(f"{path}.targetId is required for a card annotation")
            if annotation.get("status") == "active" and annotation.get("anchor", {}).get("status") == "unresolved":
                errors.append(f"{path} must expose unresolved_anchor status")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a material review report.")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_material_review(report)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print("PASS: validated material review report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
