"""Validate the one-question-per-failure Exam Hit recovery ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REASONS = {
    "question_boundary_missing", "question_text_incomplete", "source_evidence_missing", "question_unreadable",
    "mapping_missing", "card_content_incomplete", "knowledge_missing", "solution_evidence_insufficient",
    "answer_provenance_conflict",
}
STATUSES = {"OPEN", "RECOVERED", "REVALIDATED", "BLOCKED", "HANDOFF"}
ACTIONS = {"source_recovery", "mapping_repair", "knowledge_enrichment", "solution_provenance_review", "manual_review"}


def validate_tasks(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["recovery ledger must be an object"]
    errors: list[str] = []
    if data.get("schemaVersion") != "exam.hit.recovery.v1":
        errors.append("schemaVersion must be exam.hit.recovery.v1")
    if not isinstance(data.get("snapshot"), dict):
        errors.append("snapshot is required")
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return errors + ["tasks must be a list"]
    ids: set[str] = set()
    question_ids: set[str] = set()
    for index, task in enumerate(tasks):
        path = f"tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("taskId", "questionId", "failureReason", "status", "nextAction"):
            if not isinstance(task.get(field), str) or not task[field].strip():
                errors.append(f"{path}.{field} must be non-empty")
        if task.get("taskId") in ids:
            errors.append(f"{path}.taskId is duplicated")
        ids.add(task.get("taskId"))
        if task.get("questionId") in question_ids:
            errors.append(f"{path}.questionId is duplicated")
        question_ids.add(task.get("questionId"))
        if task.get("failureReason") not in REASONS:
            errors.append(f"{path}.failureReason is invalid")
        if task.get("status") not in STATUSES:
            errors.append(f"{path}.status is invalid")
        if task.get("nextAction") not in ACTIONS:
            errors.append(f"{path}.nextAction is invalid")
        if not isinstance(task.get("attempts"), list):
            errors.append(f"{path}.attempts must be a list")
        else:
            attempt_ids: set[str] = set()
            for attempt_index, attempt in enumerate(task["attempts"]):
                attempt_path = f"{path}.attempts[{attempt_index}]"
                if not isinstance(attempt, dict):
                    errors.append(f"{attempt_path} must be an object")
                    continue
                for field in ("attemptId", "questionId", "action", "status", "attemptedAt", "method"):
                    if not isinstance(attempt.get(field), str) or not attempt[field].strip():
                        errors.append(f"{attempt_path}.{field} must be non-empty")
                if attempt.get("attemptId") in attempt_ids:
                    errors.append(f"{attempt_path}.attemptId is duplicated")
                attempt_ids.add(attempt.get("attemptId"))
                if attempt.get("questionId") != task.get("questionId"):
                    errors.append(f"{attempt_path}.questionId does not match task")
                if attempt.get("status") not in {"RECOVERED", "BLOCKED", "NO_CHANGE"}:
                    errors.append(f"{attempt_path}.status is invalid")
                if not isinstance(attempt.get("evidenceRefs"), list) or not attempt["evidenceRefs"]:
                    errors.append(f"{attempt_path}.evidenceRefs must be non-empty")
    checkpoint = data.get("checkpoint")
    if checkpoint is not None:
        if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("completedTaskIds"), list) or not isinstance(checkpoint.get("remainingTaskIds"), list) or checkpoint.get("resumable") is not True:
            errors.append("checkpoint must contain completedTaskIds, remainingTaskIds, and resumable=true")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    errors = validate_tasks(json.loads(args.ledger.read_text(encoding="utf-8")))
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors))
        return 1
    print("PASS: validated Exam Hit recovery ledger.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
