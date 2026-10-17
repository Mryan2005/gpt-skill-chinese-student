"""Validate a fix report without running a full check."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


STATUSES = {"COMPLETE", "PARTIAL", "FAILED", "BLOCKED"}
EXECUTION_MODES = {"parallel-agent", "batched-agent", "shared-agent", "orchestrator-fallback"}
VALIDATION_STATUSES = {"PASS", "FAIL"}
ESCALATIONS = {"RELEARN_RECOMMENDED", "REQUIRES_UPDATE", "BLOCKED_BY_SOURCE", "FIX_NO_PROGRESS"}
MUTATION_SCOPES = {
    "derived-schema",
    "derived-provenance",
    "derived-questions",
    "derived-solutions",
    "derived-relations",
    "derived-markup",
    "runtime",
    "generated-artifact",
    "learner-state",
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_report(report: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report must be an object"]
    if report.get("schemaVersion") != "fix.report.v1":
        errors.append("schemaVersion must be fix.report.v1")
    for field in ("fixRunId", "nextAction"):
        if not _text(report.get(field)):
            errors.append(f"{field} must be non-empty")
    if report.get("nextAction") != "chinese-student: check":
        errors.append("nextAction must be chinese-student: check")
    based = report.get("basedOnCheck")
    if not isinstance(based, dict):
        errors.append("basedOnCheck is required")
    else:
        for field in ("checkRunId", "artifactVersion", "artifactHash", "schemaVersion"):
            if not _text(based.get(field)):
                errors.append(f"basedOnCheck.{field} must be non-empty")
    current = report.get("currentArtifact")
    if not isinstance(current, dict):
        errors.append("currentArtifact is required")
    else:
        for field in ("artifactVersion", "artifactHash", "schemaVersion"):
            if not _text(current.get(field)):
                errors.append(f"currentArtifact.{field} must be non-empty")
    if isinstance(based, dict) and isinstance(current, dict):
        if based.get("schemaVersion") != "check.finding.v1":
            errors.append("basedOnCheck.schemaVersion must be check.finding.v1")
        for field in ("artifactVersion", "artifactHash"):
            if based.get(field) != current.get(field):
                errors.append(f"STALE_CHECK_REPORT: basedOnCheck.{field} differs from currentArtifact")

    counts = {}
    for field in ("inputFindings", "resolved", "remaining", "blocked"):
        value = report.get(field)
        if not _non_negative_int(value):
            errors.append(f"{field} must be a non-negative integer")
        else:
            counts[field] = value
    if len(counts) == 4 and counts["inputFindings"] != counts["resolved"] + counts["remaining"] + counts["blocked"]:
        errors.append("inputFindings must equal resolved + remaining + blocked")

    changes = report.get("changes")
    if not isinstance(changes, dict):
        errors.append("changes must be an object")
    else:
        for key, value in changes.items():
            if not _non_negative_int(value):
                errors.append(f"changes.{key} must be a non-negative integer")

    execution = report.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution is required")
    else:
        if execution.get("actualMode") not in EXECUTION_MODES:
            errors.append("execution.actualMode is invalid")
        for field in ("maxParallel", "spawnFailures"):
            if not _non_negative_int(execution.get(field)):
                errors.append(f"execution.{field} must be a non-negative integer")
        if not isinstance(execution.get("spawningDisabled"), bool):
            errors.append("execution.spawningDisabled must be boolean")

    validation = report.get("localValidation")
    if not isinstance(validation, dict) or validation.get("status") not in VALIDATION_STATUSES:
        errors.append("localValidation.status must be PASS or FAIL")
    elif not isinstance(validation.get("checks"), list):
        errors.append("localValidation.checks must be a list")
    if report.get("fullCheckRun") is not None:
        errors.append("fullCheckRun must be null; fix does not run full check")
    if report.get("sourceMutation") is not False:
        errors.append("sourceMutation must be false")
    scopes = report.get("writeScopes")
    if not isinstance(scopes, list) or any(scope not in MUTATION_SCOPES for scope in scopes):
        errors.append("writeScopes contains an invalid mutation scope")

    escalations = report.get("escalations")
    if not isinstance(escalations, list):
        errors.append("escalations must be a list")
    else:
        for index, escalation in enumerate(escalations):
            if not isinstance(escalation, dict) or escalation.get("code") not in ESCALATIONS:
                errors.append(f"escalations[{index}].code is invalid")

    results = report.get("findingResults")
    if not isinstance(results, list):
        errors.append("findingResults must be a list")
    else:
        statuses = {"resolved", "remaining", "blocked"}
        if _non_negative_int(report.get("inputFindings")) and len(results) != report["inputFindings"]:
            errors.append("findingResults length must equal inputFindings")
        for index, item in enumerate(results):
            if not isinstance(item, dict) or not _text(item.get("fingerprint")):
                errors.append(f"findingResults[{index}] must have a fingerprint")
            elif item.get("status") not in statuses:
                errors.append(f"findingResults[{index}].status is invalid")

    status = report.get("status")
    if status not in STATUSES:
        errors.append("status is invalid")
    elif isinstance(counts, dict) and counts.get("resolved") is not None:
        if status == "COMPLETE" and (counts["remaining"] or counts["blocked"]):
            errors.append("COMPLETE requires no remaining or blocked findings")
        if status == "PARTIAL" and not (counts["remaining"] or counts["blocked"]):
            errors.append("PARTIAL requires remaining or blocked findings")
        if status == "COMPLETE" and validation.get("status") != "PASS":
            errors.append("COMPLETE requires localValidation PASS")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a fix report.")
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
    print(f"PASS: validated fix report {report['fixRunId']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
