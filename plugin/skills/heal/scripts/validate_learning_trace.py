"""Validate synthetic cold-start learner friction records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


FRICTION_CODES = {
    "NOT_UNDERSTOOD",
    "MISSING_PREREQUISITE",
    "STEP_TOO_LARGE",
    "NEEDS_DETAIL",
    "TOO_VERBOSE",
    "REDUNDANT",
    "MERGE_CANDIDATE",
    "SPLIT_NEEDED",
    "ORDERING_PROBLEM",
    "TERM_INTRODUCED_TOO_EARLY",
    "TRIGGER_MISSING",
    "CONDITION_MISSING",
    "COMPARISON_MISSING",
    "EXAMPLE_MISSING",
    "EXAMPLE_NOT_REPRESENTATIVE",
    "QUESTION_TOO_EARLY",
    "RETRIEVAL_FRICTION",
    "DEAD_END",
    "COGNITIVE_OVERLOAD",
}
SEVERITIES = {"high", "medium", "low"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value: Any, low: float = 0, high: float = 1) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high


def validate_trace(trace: Any) -> list[str]:
    if not isinstance(trace, dict):
        return ["trace must be an object"]
    errors: list[str] = []
    if trace.get("schemaVersion") != "heal.learning-trace.v1":
        errors.append("schemaVersion must be heal.learning-trace.v1")
    for field in ("traceId", "noviceContextId", "artifactVersion"):
        if not _text(trace.get(field)):
            errors.append(f"{field} must be non-empty")
    if trace.get("source") != "synthetic_novice":
        errors.append("source must be synthetic_novice")
    if trace.get("synthetic") is not True:
        errors.append("synthetic must be true")
    if trace.get("externalKnowledgeUsed") is not False:
        errors.append("externalKnowledgeUsed must be false")
    if trace.get("completedLearningPath") is not True:
        errors.append("completedLearningPath must be true")
    if not _number(trace.get("understandingCoverage")):
        errors.append("understandingCoverage must be between 0 and 1")
    friction = trace.get("friction")
    if not isinstance(friction, list):
        return errors + ["friction must be a list"]
    for index, item in enumerate(friction):
        path = f"friction[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("id", "entityId", "attempt", "reason", "needed"):
            if not _text(item.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if item.get("frictionCode") not in FRICTION_CODES:
            errors.append(f"{path}.frictionCode is invalid")
        if item.get("severity") not in SEVERITIES:
            errors.append(f"{path}.severity is invalid")
        if item.get("source") != "synthetic_novice":
            errors.append(f"{path}.source must be synthetic_novice")
        if item.get("synthetic") is not True:
            errors.append(f"{path}.synthetic must be true")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a synthetic heal learning trace.")
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    try:
        trace = json.loads(args.trace.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_trace(trace)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated learning trace {trace['traceId']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
