"""Apply review observations to a local JSONL file without double counting."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVENTS = {
    "correct": "independent_correct",
    "incorrect": "incorrect",
    "partially_correct": "incorrect",
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _observation(report: dict[str, Any], question: dict[str, Any]) -> dict[str, Any] | None:
    update = question.get("learnerModelUpdate", {})
    outcome = question.get("observedOutcome")
    if update.get("observation") is not True or outcome not in EVENTS:
        return None
    exam = report["exam"]
    diagnosis = question["diagnosis"]
    return {
        "id": update.get("observationId") or f"review-observation-{question['attemptId']}",
        "subjectId": exam["subjectId"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entityType": "question",
        "entityId": question["questionId"],
        "taskStage": diagnosis.get("errorStep") or "VERIFICATION",
        "event": EVENTS[outcome],
        "observedError": diagnosis.get("errorCategory"),
        "outcome": outcome,
        "source": "review",
        "attemptId": question["attemptId"],
        "examRunId": exam["examRunId"],
        "reviewRunId": report["reviewRunId"],
        "diagnosticVersion": report["diagnosticVersion"],
        "idempotencyKey": update["idempotencyKey"],
        "diagnosticStatus": diagnosis.get("diagnosticStatus"),
        "confidence": diagnosis.get("confidence"),
        "evidenceIds": diagnosis.get("evidenceRefs", []),
    }


def apply_review_observations(report: dict[str, Any], existing_lines: list[str]) -> tuple[list[str], int, int]:
    records: list[dict[str, Any]] = []
    keys: set[str] = set()
    for line in existing_lines:
        if not line.strip():
            continue
        record = json.loads(line)
        records.append(record)
        if _text(record.get("idempotencyKey")):
            keys.add(record["idempotencyKey"])
    added = 0
    skipped = 0
    for question in report.get("questions", []):
        observation = _observation(report, question)
        if observation is None:
            continue
        key = observation["idempotencyKey"]
        if key in keys:
            skipped += 1
            continue
        records.append(observation)
        keys.add(key)
        added += 1
    serialized = [json.dumps(record, ensure_ascii=False) for record in records]
    return serialized, added, skipped


def apply_review_mastery(report: dict[str, Any], mastery_state: dict[str, Any], question_state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], int, int]:
    """Merge review assessments while preserving prior history and idempotency."""
    cards = mastery_state.setdefault("reviewAssessments", {})
    questions = question_state.setdefault("questions", {})
    added = 0
    skipped = 0
    recorded_at = datetime.now(timezone.utc).isoformat()
    for item in report.get("questions", []):
        question_id = item["questionId"]
        for assessment in item.get("knowledgeMastery", []):
            card_id = assessment["cardId"]
            key = f"{report['reviewRunId']}|{question_id}|card:{card_id}|{report['diagnosticVersion']}"
            target = cards.setdefault(card_id, {"status": "unknown", "evidenceIds": [], "history": []})
            history = target.setdefault("history", [])
            if any(entry.get("idempotencyKey") == key for entry in history if isinstance(entry, dict)):
                skipped += 1
                continue
            target.update({"status": assessment["newStatus"], "evidenceIds": assessment["evidenceRefs"], "updatedAt": recorded_at})
            history.append({"idempotencyKey": key, "status": assessment["newStatus"], "evidenceIds": assessment["evidenceRefs"], "assessmentReason": assessment["assessmentReason"], "independentEvidence": assessment.get("independentEvidence", False), "recordedAt": recorded_at})
            added += 1
        assessment = item.get("questionMastery")
        if not isinstance(assessment, dict):
            continue
        key = f"{report['reviewRunId']}|{question_id}|question|{report['diagnosticVersion']}"
        target = questions.setdefault(question_id, {"status": "unknown", "evidenceIds": [], "history": []})
        history = target.setdefault("history", [])
        if any(entry.get("idempotencyKey") == key for entry in history if isinstance(entry, dict)):
            skipped += 1
            continue
        target.update({"status": assessment["newStatus"], "evidenceIds": assessment["evidenceRefs"], "updatedAt": recorded_at})
        history.append({"idempotencyKey": key, "status": assessment["newStatus"], "evidenceIds": assessment["evidenceRefs"], "assessmentReason": assessment["assessmentReason"], "independentEvidence": assessment.get("independentEvidence", False), "recordedAt": recorded_at})
        added += 1
    return mastery_state, question_state, added, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply review observations idempotently.")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--mastery", type=Path, help="Optional mastery.json to update review assessments")
    parser.add_argument("--question-mastery", type=Path, help="Optional question-mastery.json to update")
    parser.add_argument("--apply", action="store_true", help="Write the updated observations file")
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        existing = args.observations.read_text(encoding="utf-8").splitlines() if args.observations.exists() else []
        updated, added, skipped = apply_review_observations(report, existing)
        mastery_state = json.loads(args.mastery.read_text(encoding="utf-8")) if args.mastery and args.mastery.exists() else {"subjectId": report["exam"]["subjectId"], "learningEpoch": 1, "updatedAt": "", "cards": {}}
        question_state = json.loads(args.question_mastery.read_text(encoding="utf-8")) if args.question_mastery and args.question_mastery.exists() else {"subjectId": report["exam"]["subjectId"], "learningEpoch": 1, "updatedAt": "", "questions": {}}
        mastery_state, question_state, mastery_added, mastery_skipped = apply_review_mastery(report, mastery_state, question_state)
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    if args.apply:
        args.observations.parent.mkdir(parents=True, exist_ok=True)
        args.observations.write_text("\n".join(updated) + ("\n" if updated else ""), encoding="utf-8")
        if args.mastery:
            args.mastery.parent.mkdir(parents=True, exist_ok=True)
            args.mastery.write_text(json.dumps(mastery_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.question_mastery:
            args.question_mastery.parent.mkdir(parents=True, exist_ok=True)
            args.question_mastery.write_text(json.dumps(question_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"APPLIED: observations_added={added} observations_skipped={skipped} mastery_added={mastery_added} mastery_skipped={mastery_skipped} path={args.observations}")
    else:
        print(f"DRY_RUN: observations_added={added} observations_skipped={skipped} mastery_added={mastery_added} mastery_skipped={mastery_skipped}. Use --apply to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
