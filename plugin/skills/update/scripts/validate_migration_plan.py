"""Validate an idempotent, source-safe update migration plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


OUTCOMES = {
    "UP_TO_DATE",
    "MIGRATION_REQUIRED",
    "INCOMPATIBLE",
    "UNKNOWN_LEGACY",
    "NEEDS_REDERIVATION",
    "BLOCKED_BY_SOURCE",
    "MIGRATED_WITH_ERRORS",
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_plan(plan: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["plan must be an object"]
    if plan.get("schemaVersion") != "update-plan.v1":
        errors.append("schemaVersion must be update-plan.v1")
    if not isinstance(plan.get("subject"), dict) or not _text(plan["subject"].get("id")):
        errors.append("subject.id is required")
    if plan.get("status") not in OUTCOMES:
        errors.append("status is invalid")
    current = plan.get("current")
    target = plan.get("target")
    for name, metadata in (("current", current), ("target", target)):
        if not isinstance(metadata, dict):
            errors.append(f"{name} metadata is required")
            continue
        for field in ("pluginVersion", "contentSchemaVersion", "domainSchemaVersion", "rendererVersion", "sourceVersion", "derivedVersion"):
            if field not in metadata:
                errors.append(f"{name}.{field} is required")
    steps = plan.get("steps")
    if not isinstance(steps, list):
        errors.append("steps must be a list")
        steps = []
    step_ids: set[str] = set()
    for index, step in enumerate(steps):
        path = f"steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{path} must be an object")
            continue
        step_id = step.get("id")
        if not _text(step_id):
            errors.append(f"{path}.id is required")
        elif step_id in step_ids:
            errors.append(f"{path}.id is duplicated")
        else:
            step_ids.add(step_id)
        if step.get("kind") not in {"generic", "domain"}:
            errors.append(f"{path}.kind must be generic or domain")
        for field in ("owner", "fromVersion", "toVersion", "status"):
            if field not in step:
                errors.append(f"{path}.{field} is required")
        if step.get("idempotent") is not True:
            errors.append(f"{path}.idempotent must be true")
        if step.get("sourceMutation") != "forbidden":
            errors.append(f"{path}.sourceMutation must be forbidden")
        if not isinstance(step.get("requiresSourceReread"), bool):
            errors.append(f"{path}.requiresSourceReread must be boolean")
        if not isinstance(step.get("requiresArtifactRebuild"), bool):
            errors.append(f"{path}.requiresArtifactRebuild must be boolean")
    snapshot = plan.get("snapshot")
    if not isinstance(snapshot, dict) or not _text(snapshot.get("id")):
        errors.append("snapshot.id is required")
    impact = plan.get("impact")
    if not isinstance(impact, dict):
        errors.append("impact is required")
    if plan.get("finalGate") != "check":
        errors.append("finalGate must be check")
    if isinstance(current, dict) and isinstance(target, dict):
        current_key = tuple(current.get(field) for field in ("pluginVersion", "contentSchemaVersion", "domainSchemaVersion", "rendererVersion"))
        target_key = tuple(target.get(field) for field in ("pluginVersion", "contentSchemaVersion", "domainSchemaVersion", "rendererVersion"))
        if current_key == target_key:
            if plan.get("status") != "UP_TO_DATE":
                errors.append("same current/target versions require UP_TO_DATE")
            if steps:
                errors.append("UP_TO_DATE plan must have no migration steps")
        elif plan.get("status") == "UP_TO_DATE":
            errors.append("different current/target versions require migration")
            if not steps:
                errors.append("MIGRATION_REQUIRED plan needs steps")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an update migration plan.")
    parser.add_argument("plan", type=Path)
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_plan(plan)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated migration plan with status {plan['status']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
