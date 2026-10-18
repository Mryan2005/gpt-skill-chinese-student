"""Validate a user-directed amendment report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STATUSES = {"COMPLETE", "PARTIAL", "BLOCKED", "FAILED"}
VALIDATION_STATUSES = {"PASS", "FAIL"}
ESCALATIONS = {"NEEDS_CLARIFICATION", "BLOCKED_BY_SOURCE", "RELEARN_REQUIRED", "UPDATE_REQUIRED"}
LAYERS = {
    "derived-card",
    "derived-solution",
    "question-mapping",
    "relation",
    "source-transcription",
    "runtime",
    "generated-markdown",
    "generated-html",
    "learner-derived",
}
ACTIONS = {"add", "replace", "recompute", "reclassify", "repair"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _changes(value: Any, field: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list) or not value:
        return [f"{field} must be a non-empty list"]
    for index, item in enumerate(value):
        path = f"{field}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        for required in ("layer", "entityId", "action"):
            if not _text(item.get(required)):
                errors.append(f"{path}.{required} must be non-empty")
        if item.get("layer") not in LAYERS:
            errors.append(f"{path}.layer is invalid")
        if item.get("action") not in ACTIONS:
            errors.append(f"{path}.action is invalid")
        if item.get("provenance") != "user_feedback":
            errors.append(f"{path}.provenance must be user_feedback")
    return errors


def validate_report(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") != "amend.report.v1":
        errors.append("schemaVersion must be amend.report.v1")
    for field in ("amendRunId", "nextAction"):
        if not _text(report.get(field)):
            errors.append(f"{field} must be non-empty")
    if report.get("nextAction") != "run check":
        errors.append("nextAction must be run check")
    if report.get("status") not in STATUSES:
        errors.append("status is invalid")

    request = report.get("request")
    if not isinstance(request, dict):
        errors.append("request is required")
    else:
        if request.get("source") != "user_feedback":
            errors.append("request.source must be user_feedback")
        if not _text(request.get("text")):
            errors.append("request.text must be non-empty")
        if not isinstance(request.get("targets"), list) or not request["targets"] or any(not _text(item) for item in request["targets"]):
            errors.append("request.targets must contain target IDs")

    errors.extend(_changes(report.get("plan"), "plan"))
    errors.extend(_changes(report.get("changes"), "changes"))
    if report.get("sourceMutation") is not False:
        errors.append("sourceMutation must be false")
    if report.get("officialProvenanceMutation") is not False:
        errors.append("officialProvenanceMutation must be false")

    validation = report.get("localValidation")
    if not isinstance(validation, dict) or validation.get("status") not in VALIDATION_STATUSES:
        errors.append("localValidation.status must be PASS or FAIL")
    elif not isinstance(validation.get("checks"), list) or not validation["checks"]:
        errors.append("localValidation.checks must be non-empty")

    history = report.get("history")
    if not isinstance(history, dict) or history.get("path") != "history/amendments.jsonl" or history.get("recorded") is not True:
        errors.append("history must record history/amendments.jsonl")

    escalations = report.get("escalations")
    if not isinstance(escalations, list) or any(not isinstance(item, dict) or item.get("code") not in ESCALATIONS for item in escalations):
        errors.append("escalations contains an invalid code")
    if report.get("status") == "COMPLETE" and validation.get("status") != "PASS":
        errors.append("COMPLETE requires localValidation PASS")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an amendment report.")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_report(report)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated amendment report {report['amendRunId']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
