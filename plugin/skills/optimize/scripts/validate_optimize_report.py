"""Validate a safe, evidence-backed Chinese Student optimization report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


OPERATION_TYPES = {
    "exact_duplicate",
    "fragmented_merge",
    "semantic_merge",
    "oversized_split",
    "related_but_distinct",
    "uncertain",
}
HIGH_RISK_TYPES = {"fragmented_merge", "semantic_merge", "oversized_split", "uncertain"}
DECISIONS = {"NO_OP", "RECOMMEND", "APPROVE", "APPLIED", "BLOCKED"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list(value: Any) -> bool:
    return isinstance(value, list)


def validate_report(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") != "optimize.report.v1":
        errors.append("schemaVersion is invalid")
    for field in ("optimizeRunId", "subjectId", "currentStateSha256"):
        if not _text(report.get(field)):
            errors.append(f"{field} must be non-empty")
    if report.get("mode") not in {"analyze", "apply", "verify"}:
        errors.append("mode is invalid")
    if report.get("status") not in {"NO_OP", "RECOMMENDATIONS", "APPROVED", "APPLIED", "BLOCKED", "FAILED"}:
        errors.append("status is invalid")
    for field in ("sourcePreserved", "examResultPreserved", "learnerStatePreserved"):
        if report.get(field) is not True:
            errors.append(f"{field} must be true")

    operations = report.get("operations")
    operation_ids: set[str] = set()
    if not _list(operations):
        errors.append("operations must be a list")
        operations = []
    for index, operation in enumerate(operations):
        path = f"operations[{index}]"
        if not isinstance(operation, dict):
            errors.append(f"{path} must be an object")
            continue
        operation_id = operation.get("operationId")
        if not _text(operation_id):
            errors.append(f"{path}.operationId must be non-empty")
        elif operation_id in operation_ids:
            errors.append(f"{path}.operationId is duplicated")
        else:
            operation_ids.add(operation_id)
        if operation.get("type") not in OPERATION_TYPES:
            errors.append(f"{path}.type is invalid")
        if not isinstance(operation.get("targetIds"), list) or not operation["targetIds"]:
            errors.append(f"{path}.targetIds must be non-empty")
        if operation.get("risk") not in {"low", "medium", "high"}:
            errors.append(f"{path}.risk is invalid")
        if operation.get("decision") not in DECISIONS:
            errors.append(f"{path}.decision is invalid")
        if not isinstance(operation.get("requiresConfirmation"), bool):
            errors.append(f"{path}.requiresConfirmation must be boolean")
        if not isinstance(operation.get("evidenceRefs"), list) or not operation["evidenceRefs"]:
            errors.append(f"{path}.evidenceRefs must be non-empty")
        if not _text(operation.get("reason")):
            errors.append(f"{path}.reason must be non-empty")
        if operation.get("type") in HIGH_RISK_TYPES and operation.get("requiresConfirmation") is not True:
            errors.append(f"{path} high-risk operation requires confirmation")
        if operation.get("type") == "exact_duplicate" and operation.get("requiresConfirmation") is True:
            errors.append(f"{path} exact duplicate should not require semantic confirmation")

    confirmation = report.get("confirmation")
    if not isinstance(confirmation, dict) or not isinstance(confirmation.get("required"), bool) or not isinstance(confirmation.get("received"), bool):
        errors.append("confirmation must include boolean required and received")
    elif report.get("mode") == "apply" and confirmation["received"] is not True:
        errors.append("apply mode requires explicit confirmation")
    migration = report.get("migration")
    if not isinstance(migration, dict):
        errors.append("migration is required")
    else:
        for field in ("cardAliases", "cardIdMappings", "relationRemaps", "questionMappingRemaps", "learnerStateEffects"):
            if not isinstance(migration.get(field), list):
                errors.append(f"migration.{field} must be a list")
        nested_validation = migration.get("validation")
        if not isinstance(nested_validation, dict) or nested_validation.get("status") not in {"PASS", "FAIL", "BLOCKED"}:
            errors.append("migration.validation.status is invalid")
        aliases = migration.get("cardAliases", []) if isinstance(migration, dict) else []
        for index, alias in enumerate(aliases):
            if not isinstance(alias, dict) or not _text(alias.get("oldId")) or not _text(alias.get("newId")) or alias.get("oldId") == alias.get("newId"):
                errors.append(f"migration.cardAliases[{index}] is invalid")

    validation = report.get("validation")
    if not isinstance(validation, dict) or validation.get("status") not in {"PASS", "FAIL", "BLOCKED"} or not isinstance(validation.get("idempotent"), bool):
        errors.append("validation must contain status and idempotent")
    if report.get("status") == "APPLIED" and report.get("mode") != "apply":
        errors.append("APPLIED status requires apply mode")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Chinese Student optimize report.")
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
    print("PASS: validated optimize report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
