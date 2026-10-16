"""Validate the frozen-state exam record and its state-machine invariants."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STATES = [
    "READY",
    "SNAPSHOT_FROZEN",
    "FIRST_PASS",
    "ANSWERS_FROZEN",
    "SOLUTION_RELEASED",
    "GRADING",
    "POSTMORTEM",
    "CLOSED",
]
RESULTS = {"correct", "wrong", "unanswered", "partial"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record(record: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record must be an object"]
    if record.get("schemaVersion") != "exam-record.v1":
        errors.append("schemaVersion must be exam-record.v1")
    state = record.get("state")
    if state not in STATES:
        errors.append(f"state is invalid: {state}")
        state_index = -1
    else:
        state_index = STATES.index(state)
    if not isinstance(record.get("readOnlyDuringMeasurement"), bool):
        errors.append("readOnlyDuringMeasurement must be boolean")
    snapshot = record.get("snapshot")
    if not isinstance(snapshot, dict):
        errors.append("snapshot is required")
    else:
        for field in ("id", "subjectId", "artifactVersion", "frozenAt"):
            if not _text(snapshot.get(field)):
                errors.append(f"snapshot.{field} is required")
        if state_index >= STATES.index("SNAPSHOT_FROZEN") and snapshot.get("frozen") is not True:
            errors.append("snapshot.frozen must be true after SNAPSHOT_FROZEN")

    questions = record.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append("questions must be a non-empty list")
        questions = []
    question_ids: set[str] = set()
    for index, question in enumerate(questions):
        path = f"questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{path} must be an object")
            continue
        question_id = question.get("questionId")
        if not _text(question_id):
            errors.append(f"{path}.questionId is required")
        elif question_id in question_ids:
            errors.append(f"{path}.questionId is duplicated: {question_id}")
        else:
            question_ids.add(question_id)
        first_pass = question.get("firstPass")
        if state_index >= STATES.index("FIRST_PASS"):
            if not isinstance(first_pass, dict):
                errors.append(f"{path}.firstPass is required from FIRST_PASS onward")
            else:
                for field in ("answer", "confidence", "reasoningSummary", "order"):
                    if field not in first_pass:
                        errors.append(f"{path}.firstPass.{field} is required")
        if state_index >= STATES.index("ANSWERS_FROZEN") and question.get("firstPassFrozen") is not True:
            errors.append(f"{path}.firstPassFrozen must be true after ANSWERS_FROZEN")
        grading = question.get("grading")
        if state_index >= STATES.index("GRADING"):
            if not isinstance(grading, dict):
                errors.append(f"{path}.grading is required from GRADING onward")
            elif grading.get("result") not in RESULTS:
                errors.append(f"{path}.grading.result is invalid")
        revisions = question.get("revisions", [])
        if not isinstance(revisions, list):
            errors.append(f"{path}.revisions must be a list")

    access_log = record.get("accessLog", [])
    if not isinstance(access_log, list):
        errors.append("accessLog must be a list")
    else:
        for index, entry in enumerate(access_log):
            if not isinstance(entry, dict):
                errors.append(f"accessLog[{index}] must be an object")
                continue
            phase = entry.get("phase")
            source = entry.get("source")
            if phase == "FIRST_PASS" and source in {"web", "solution", "answer_key", "unfrozen_subject"}:
                errors.append(f"accessLog[{index}] violates FIRST_PASS access policy")

    for field in ("officialAnswersReleasedAt", "gradingCompletedAt", "closedAt"):
        if field in record and record[field] is not None and not _text(record[field]):
            errors.append(f"{field} must be a timestamp string or null")
    if state_index >= STATES.index("SOLUTION_RELEASED") and not _text(record.get("officialAnswersReleasedAt")):
        errors.append("officialAnswersReleasedAt is required after SOLUTION_RELEASED")
    if state_index >= STATES.index("CLOSED"):
        for field in ("performance", "knowledgeCoverage", "graphEffectiveness", "errorProfile", "repairRequests"):
            if field not in record:
                errors.append(f"{field} is required for CLOSED record")
    repair_requests = record.get("repairRequests", [])
    if not isinstance(repair_requests, list):
        errors.append("repairRequests must be a list")
    else:
        for index, request in enumerate(repair_requests):
            if not isinstance(request, dict):
                errors.append(f"repairRequests[{index}] must be an object")
                continue
            if request.get("owner") not in {"learn", "study-math", "domain-model"}:
                errors.append(f"repairRequests[{index}].owner must route to learn or a domain model")
            for field in ("questionId", "reason", "evidence"):
                if not _text(request.get(field)):
                    errors.append(f"repairRequests[{index}].{field} is required")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a frozen-state exam record.")
    parser.add_argument("record", type=Path)
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_record(record)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated exam record in state {record['state']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
