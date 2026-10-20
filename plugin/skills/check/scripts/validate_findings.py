"""Validate the read-only structured finding report produced by check."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any



PLUGIN_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(PLUGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SCRIPTS))

from agent_roles import load_agent_role_registry, validate_agent_role_registry  # noqa: E402

SEVERITIES = {"blocker", "error", "warning", "info"}
RESULTS = {"PASS", "PASS_WITH_WARNINGS", "FAIL", "BLOCKED"}
AUDIT_STATUSES = {"PASS", "WARNING", "FAIL", "BLOCKED"}
EXECUTION_MODES = {"parallel-agent", "batched-agent", "shared-agent", "orchestrator-fallback"}


def _load_check_roles() -> tuple[set[str], set[str], set[str]]:
    plugin_root = Path(__file__).resolve().parents[3]
    registry = load_agent_role_registry(plugin_root)
    errors = validate_agent_role_registry(registry, plugin_root)
    if errors:
        raise ValueError("invalid Agent Role Registry: " + " | ".join(errors))
    workflow = next(item for item in registry["workflows"] if item["skill"] == "check")
    bundles = workflow["bundles"]
    role_ids = {role["id"] for role in workflow["roles"]}
    reporters = role_ids | {workflow["mergerRole"]}
    auditors = {role_id.removesuffix("-auditor") for role_id in role_ids if role_id != workflow["mergerRole"]}
    return set(bundles), auditors, reporters


WORKER_BUNDLES, AUDITORS, REPORTERS = _load_check_roles()
REQUIRED_BY_MODE = {
    "full-audit": AUDITORS,
    "source-audit": {"source", "provenance"},
    "content-audit": {"content", "coverage"},
    "question-audit": {"question", "solution", "provenance", "math"},
    "latex-audit": {"latex"},
    "relation-audit": {"relation"},
    "rendering-audit": {"rendering"},
    "retrieval-audit": {"retrieval"},
}
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
    workspace = report.get("workspace")
    if not isinstance(workspace, dict):
        errors.append("CHECK_WORKSPACE_NOT_CLEAN: workspace is required")
    else:
        if workspace.get("root") != ".check/current":
            errors.append("CHECK_WORKSPACE_NOT_CLEAN: workspace.root must be .check/current")
        if workspace.get("previousRunDeleted") is not True or workspace.get("cleanVerified") is not True:
            errors.append("CHECK_WORKSPACE_NOT_CLEAN: workspace must record reset and clean verification")
        if workspace.get("residualPaths") != []:
            errors.append("CHECK_WORKSPACE_NOT_CLEAN: residualPaths must be empty")
    artifact = report.get("artifact")
    if (
        not isinstance(artifact, dict)
        or not _text(artifact.get("version"))
        or not _text(artifact.get("hash"))
        or not _text(artifact.get("checkedAt"))
    ):
        errors.append("artifact.version, artifact.hash, and artifact.checkedAt are required")
    execution = report.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution is required")
    else:
        if execution.get("requestedMode") != "multi-agent":
            errors.append("execution.requestedMode must be multi-agent")
        if execution.get("actualMode") not in EXECUTION_MODES:
            errors.append("execution.actualMode is invalid")
        for field in ("maxParallel", "maxConsecutiveSpawnFailures", "spawnFailures"):
            value = execution.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"execution.{field} must be a non-negative integer")
        if execution.get("maxParallel", 0) > 3:
            errors.append("execution.maxParallel cannot exceed 3")
        if not isinstance(execution.get("spawningDisabled"), bool):
            errors.append("execution.spawningDisabled must be boolean")
        if execution.get("spawnFailures", 0) >= 2 and execution.get("spawningDisabled") is not True:
            errors.append("execution.spawningDisabled must be true after two spawn failures")
        if execution.get("actualMode") == "orchestrator-fallback" and not _text(execution.get("fallbackReason")):
            errors.append("execution.fallbackReason is required for orchestrator-fallback")
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
        if finding.get("reportedBy") not in REPORTERS:
            errors.append(f"{path}.reportedBy is invalid")
        for field in ("reportedBy", "code", "subject", "entityType", "entityId", "observed", "expected", "rootLayer", "repairOwner"):
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
    run = report.get("run")
    audit_statuses = run.get("auditStatuses") if isinstance(run, dict) else None
    observed_auditors: set[str] = set()
    audit_has_fail = False
    audit_has_warning = False
    audit_has_blocked = False
    if not isinstance(audit_statuses, list):
        errors.append("run.auditStatuses must be a list")
    else:
        for index, audit in enumerate(audit_statuses):
            path = f"run.auditStatuses[{index}]"
            if not isinstance(audit, dict):
                errors.append(f"{path} must be an object")
                continue
            auditor = audit.get("auditor")
            if auditor not in AUDITORS:
                errors.append(f"{path}.auditor is invalid")
            elif auditor in observed_auditors:
                errors.append(f"{path}.auditor is duplicated: {auditor}")
            else:
                observed_auditors.add(auditor)
            status = audit.get("auditStatus")
            if status not in AUDIT_STATUSES:
                errors.append(f"{path}.auditStatus is invalid")
            elif status == "FAIL":
                audit_has_fail = True
            elif status == "WARNING":
                audit_has_warning = True
            elif status == "BLOCKED":
                audit_has_blocked = True
            if audit.get("executionMode") not in EXECUTION_MODES:
                errors.append(f"{path}.executionMode is invalid")
            if audit.get("workerBundle") not in WORKER_BUNDLES:
                errors.append(f"{path}.workerBundle is invalid")
        mode = run.get("mode") if isinstance(run, dict) else None
        required = REQUIRED_BY_MODE.get(mode)
        if required and required - observed_auditors:
            errors.append(f"AUDIT_SCOPE_INCOMPLETE: missing {', '.join(sorted(required - observed_auditors))}")
    result = report.get("result")
    if result not in RESULTS:
        errors.append("result must be PASS, PASS_WITH_WARNINGS, FAIL, or BLOCKED")
    else:
        workspace_invalid = not isinstance(workspace, dict) or workspace.get("residualPaths") != []
        expected_result = "BLOCKED" if workspace_invalid or audit_has_blocked else (
            "FAIL" if actual["blocker"] or actual["error"] or audit_has_fail else (
                "PASS_WITH_WARNINGS" if actual["warning"] or audit_has_warning else "PASS"
            )
        )
        if result != expected_result:
            errors.append(f"result={result} does not match expected {expected_result}")
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
