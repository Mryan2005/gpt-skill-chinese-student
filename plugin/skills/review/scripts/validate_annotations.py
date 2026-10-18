"""Validate Review Annotation Overlay records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


HIGHLIGHT_TYPES = {"high_frequency", "confirmed_weakness", "suspected_weakness", "confusion", "prerequisite_gap", "error_step", "must_memorize", "must_understand", "must_practice", "key_source_span", "scoring_point", "retest_target"}
PRIORITIES = {"critical", "high", "medium", "low"}
STRENGTHS = {"confirmed", "supported", "tentative", "unknown"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_overlay(overlay: Any) -> list[str]:
    if not isinstance(overlay, dict):
        return ["overlay must be an object"]
    errors: list[str] = []
    if overlay.get("schemaVersion") != "review.annotation-overlay.v1":
        errors.append("schemaVersion must be review.annotation-overlay.v1")
    for field in ("subjectId", "reviewRunId"):
        if not _text(overlay.get(field)):
            errors.append(f"{field} must be non-empty")
    annotations = overlay.get("annotations")
    if not isinstance(annotations, list):
        return errors + ["annotations must be a list"]
    seen: set[str] = set()
    for index, annotation in enumerate(annotations):
        path = f"annotations[{index}]"
        if not isinstance(annotation, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("highlightId", "targetType", "targetId", "reason", "renderHint"):
            if not _text(annotation.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if annotation.get("highlightId") in seen:
            errors.append(f"{path}.highlightId is duplicated")
        seen.add(annotation.get("highlightId"))
        if annotation.get("highlightType") not in HIGHLIGHT_TYPES:
            errors.append(f"{path}.highlightType is invalid")
        if annotation.get("priority") not in PRIORITIES:
            errors.append(f"{path}.priority is invalid")
        if annotation.get("evidenceStrength") not in STRENGTHS:
            errors.append(f"{path}.evidenceStrength is invalid")
        if not isinstance(annotation.get("evidenceRefs"), list) or not annotation["evidenceRefs"]:
            errors.append(f"{path}.evidenceRefs must be non-empty")
        if annotation.get("status") not in {"active", "resolved", "stale", "unresolved_anchor"}:
            errors.append(f"{path}.status is invalid")
        if annotation.get("highlightType") == "confirmed_weakness" and annotation.get("evidenceStrength") not in {"confirmed", "supported"}:
            errors.append(f"{path}.confirmed_weakness needs confirmed or supported evidence")
        if annotation.get("highlightType") == "suspected_weakness" and annotation.get("evidenceStrength") not in {"tentative", "unknown"}:
            errors.append(f"{path}.suspected_weakness should remain tentative or unknown")
        anchor = annotation.get("anchor")
        if annotation.get("status") == "unresolved_anchor" and isinstance(anchor, dict) and anchor.get("status") == "resolved":
            errors.append(f"{path}.unresolved_anchor cannot have a resolved anchor")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an annotation overlay.")
    parser.add_argument("overlay", type=Path)
    args = parser.parse_args()
    try:
        overlay = json.loads(args.overlay.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_overlay(overlay)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print("PASS: validated annotation overlay.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
