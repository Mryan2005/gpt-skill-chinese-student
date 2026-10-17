"""Validate isolated reports written by check's specialized auditors."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


AGENTS = {
    "source-auditor",
    "structure-auditor",
    "content-auditor",
    "coverage-auditor",
    "question-auditor",
    "solution-auditor",
    "math-auditor",
    "latex-auditor",
    "relation-auditor",
    "provenance-auditor",
    "rendering-auditor",
    "retrieval-auditor",
    "learner-model-auditor",
    "sort-state-auditor",
}
SEVERITIES = {"blocker", "error", "warning", "info"}
STATUSES = {"completed", "skipped", "failed"}
EXECUTION_MODES = {"parallel-agent", "batched-agent", "shared-agent", "orchestrator-fallback"}
REQUIRED_FINDING_FIELDS = {
    "id",
    "reportedBy",
    "code",
    "severity",
    "subject",
    "entityType",
    "entityId",
    "observed",
    "expected",
    "evidence",
    "rootLayer",
    "repairOwner",
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _evidence(value: Any) -> bool:
    if _text(value):
        return True
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, dict) and any(_text(part) for part in item.values()) for item in value
    )


def validate_agent_report(
    report: Any,
    *,
    expected_run_id: str | None = None,
    expected_artifact_version: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report must be an object"]
    if report.get("schemaVersion") != "check.agent-report.v1":
        errors.append("schemaVersion must be check.agent-report.v1")
    if report.get("agentId") not in AGENTS:
        errors.append("agentId must identify one specialized auditor")
    for field in ("runId", "artifactVersion"):
        if not _text(report.get(field)):
            errors.append(f"{field} must be non-empty")
    if expected_run_id is not None and report.get("runId") != expected_run_id:
        errors.append("STALE_AGENT_REPORT: runId does not match the current run")
    if expected_artifact_version is not None and report.get("artifactVersion") != expected_artifact_version:
        errors.append("STALE_AGENT_REPORT: artifactVersion does not match the current artifact")
    if report.get("readOnly") is not True:
        errors.append("readOnly must be true")
    if report.get("status") not in STATUSES:
        errors.append("status must be completed, skipped, or failed")
    if report.get("executionMode") not in EXECUTION_MODES:
        errors.append("executionMode is invalid")
    for field in ("checkedPaths", "executedChecks", "skippedChecks"):
        if not isinstance(report.get(field), list):
            errors.append(f"{field} must be a list")
    if report.get("status") in {"skipped", "failed"} and not report.get("skippedChecks"):
        errors.append("skippedChecks must explain a skipped or failed auditor")

    findings = report.get("findings")
    if not isinstance(findings, list):
        return errors + ["findings must be a list"]
    seen_ids: set[str] = set()
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
        if finding.get("severity") not in SEVERITIES:
            errors.append(f"{path}.severity is invalid")
        if finding.get("reportedBy") != report.get("agentId"):
            errors.append(f"{path}.reportedBy must match the report agentId")
        for field in ("reportedBy", "code", "subject", "entityType", "entityId", "observed", "expected", "rootLayer", "repairOwner"):
            if not _text(finding.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if not _evidence(finding.get("evidence")):
            errors.append(f"{path}.evidence must contain a location or evidence object")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an isolated check auditor report.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--artifact-version")
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_agent_report(
        report,
        expected_run_id=args.run_id,
        expected_artifact_version=args.artifact_version,
    )
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated {len(report['findings'])} finding(s) from {report['agentId']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
