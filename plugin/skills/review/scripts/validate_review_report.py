"""Validate an Exam Result postmortem report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STAGES = {"RETRIEVAL", "METHOD_SELECTION", "CONDITION_CHECK", "SETUP", "EXECUTION", "VERIFICATION", "EXPRESSION", "READING", "MEMORY", "TIME", "SOURCE_ISSUE"}
ROUTES = {"learner_model", "amend", "check", "fix", "heal", "none"}
STATUSES = {"COMPLETE", "PARTIAL", "BLOCKED", "FAILED"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_report(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") != "review.report.v1":
        errors.append("schemaVersion must be review.report.v1")
    for field in ("reviewRunId", "source"):
        if not _text(report.get(field)):
            errors.append(f"{field} must be non-empty")
    if report.get("source") != "exam_result":
        errors.append("source must be exam_result")
    if report.get("status") not in STATUSES:
        errors.append("status is invalid")

    exam = report.get("exam")
    if not isinstance(exam, dict):
        errors.append("exam is required")
    else:
        for field in ("examRunId", "subjectId", "artifactVersion", "artifactHash", "resultPath"):
            if not _text(exam.get(field)):
                errors.append(f"exam.{field} must be non-empty")
        if exam.get("answersFrozen") is not True:
            errors.append("exam.answersFrozen must be true")

    questions = report.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append("questions must be a non-empty list")
        questions = []
    for index, item in enumerate(questions):
        path = f"questions[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        if not _text(item.get("questionId")):
            errors.append(f"{path}.questionId must be non-empty")
        if not isinstance(item.get("correct"), bool):
            errors.append(f"{path}.correct must be boolean")
        diagnosis = item.get("diagnosis")
        if not isinstance(diagnosis, dict):
            errors.append(f"{path}.diagnosis is required")
        else:
            if diagnosis.get("stage") not in STAGES:
                errors.append(f"{path}.diagnosis.stage is invalid")
            for field in ("errorCode", "reason"):
                if not _text(diagnosis.get(field)):
                    errors.append(f"{path}.diagnosis.{field} must be non-empty")
            if not isinstance(diagnosis.get("evidenceIds"), list) or not diagnosis["evidenceIds"]:
                errors.append(f"{path}.diagnosis.evidenceIds must be non-empty")
        if item.get("route") not in ROUTES:
            errors.append(f"{path}.route is invalid")
        update = item.get("learnerModelUpdate")
        if not isinstance(update, dict) or not isinstance(update.get("observation"), bool):
            errors.append(f"{path}.learnerModelUpdate.observation must be boolean")
        remediation = item.get("remediation")
        if not isinstance(remediation, dict) or not isinstance(remediation.get("cards"), list) or not isinstance(remediation.get("strategy"), list):
            errors.append(f"{path}.remediation must contain cards and strategy lists")

    model = report.get("learnerModel")
    if not isinstance(model, dict):
        errors.append("learnerModel is required")
    else:
        if not _non_negative_int(model.get("observationsAppended")):
            errors.append("learnerModel.observationsAppended must be non-negative")
        if model.get("historicalObservationsPreserved") is not True:
            errors.append("learnerModel.historicalObservationsPreserved must be true")
        if not isinstance(model.get("updatedPaths"), list):
            errors.append("learnerModel.updatedPaths must be a list")

    for field in ("routing", "localValidation"):
        if not isinstance(report.get(field), dict):
            errors.append(f"{field} is required")
    validation = report.get("localValidation")
    if isinstance(validation, dict) and validation.get("status") not in {"PASS", "FAIL"}:
        errors.append("localValidation.status must be PASS or FAIL")
    if report.get("examResultMutation") is not False:
        errors.append("examResultMutation must be false")
    if report.get("artifactMutation") is not False:
        errors.append("artifactMutation must be false")
    if not isinstance(report.get("nextActions"), list):
        errors.append("nextActions must be a list")
    if report.get("fullCheckRun") is not None:
        errors.append("fullCheckRun must be null; review does not run full check")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a review report.")
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
    print(f"PASS: validated review report {report['reviewRunId']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
