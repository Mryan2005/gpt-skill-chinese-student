"""Validate the closed Exam Result boundary consumed by review."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ATTEMPT_STATUSES = {"ANSWERED", "UNANSWERED_BY_LEARNER", "NOT_ATTEMPTED", "BLOCKED_BY_SOURCE", "BLOCKED_BY_MAPPING", "SKIPPED_BY_EXAM"}
GRADING_STATUSES = {"GRADED", "UNGRADED", "BLOCKED"}
ARTIFACT_STATUSES = {"OK", "GRAPH_MAPPING_MISSING", "GRAPH_MAPPING_AMBIGUOUS", "SOURCE_MISSING", "SOURCE_INCOMPLETE", "ANSWER_PROVENANCE_CONFLICT", "QUESTION_UNREADABLE", "REFERENCE_ANSWER_MISSING"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_exam_result(result: Any) -> list[str]:
    if not isinstance(result, dict):
        return ["Exam Result must be an object"]
    errors: list[str] = []
    if result.get("status") != "CLOSED":
        errors.append("REVIEW_INPUT_NOT_CLOSED: status must be CLOSED")
    for field in ("examRunId", "subjectId", "examResultHash"):
        if not _text(result.get(field)):
            errors.append(f"{field} must be non-empty")
    questions = result.get("questions")
    if not isinstance(questions, list) or not questions:
        return errors + ["questions must be a non-empty list"]
    seen: set[str] = set()
    for index, question in enumerate(questions):
        path = f"questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("questionId", "attemptId"):
            if not _text(question.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if question.get("attemptId") in seen:
            errors.append(f"{path}.attemptId is duplicated")
        seen.add(question.get("attemptId"))
        if question.get("attemptStatus") not in ATTEMPT_STATUSES:
            errors.append(f"{path}.attemptStatus is invalid")
        if question.get("gradingStatus") not in GRADING_STATUSES:
            errors.append(f"{path}.gradingStatus is invalid")
        if question.get("artifactStatus") not in ARTIFACT_STATUSES:
            errors.append(f"{path}.artifactStatus is invalid")
        if not isinstance(question.get("learnerAttributionEligible"), bool):
            errors.append(f"{path}.learnerAttributionEligible must be boolean")
        blockers = question.get("artifactStatus") != "OK" or question.get("gradingStatus") != "GRADED" or question.get("attemptStatus") not in {"ANSWERED", "UNANSWERED_BY_LEARNER"}
        if question.get("learnerAttributionEligible") and blockers:
            errors.append(f"{path}.LEARNER_ATTRIBUTION_GATE violated")
        if question.get("learnerAttributionEligible") and question.get("attemptStatus") == "UNANSWERED_BY_LEARNER":
            errors.append(f"{path}.unanswered learner attribution requires explicit review evidence")
        if question.get("answerConflict") is True and question.get("learnerAttributionEligible"):
            errors.append(f"{path}.answer conflict cannot be learner-attribution eligible")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a closed Exam Result for review.")
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        result = json.loads(args.result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_exam_result(result)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated closed Exam Result {result['examRunId']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
