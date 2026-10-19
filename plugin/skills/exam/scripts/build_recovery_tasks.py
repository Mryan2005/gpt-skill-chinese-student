"""Classify every non-complete Exam Hit record into an actionable recovery task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FAILURE_REASONS = {
    "question_boundary_missing",
    "question_text_incomplete",
    "source_evidence_missing",
    "question_unreadable",
    "mapping_missing",
    "card_content_incomplete",
    "knowledge_missing",
    "solution_evidence_insufficient",
    "answer_provenance_conflict",
}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def classify(question: dict[str, Any]) -> str:
    result = question.get("hitResult", {})
    explicit = _text(result.get("failureReason"))
    if explicit in FAILURE_REASONS:
        return explicit
    issues = " ".join(str(item).casefold() for item in result.get("mappingIssues", []) if isinstance(result.get("mappingIssues"), list))
    unresolved = " ".join(str(value).casefold() for value in (result.get("unresolvedReason"), result.get("supportedReasoning")) if value)
    if "answer" in issues or "conflict" in issues:
        return "answer_provenance_conflict"
    if question.get("readStatus") == "UNREADABLE":
        return "question_unreadable"
    if "boundary" in unresolved or "isolate" in unresolved or "structure" in unresolved:
        return "question_boundary_missing"
    if "unreadable" in unresolved or "read" in unresolved:
        return "question_unreadable"
    if "source" in issues or "provenance" in issues:
        return "source_evidence_missing"
    if "mapping" in issues or "direct_mapping" in issues:
        return "mapping_missing"
    if result.get("hitStatus") == "PARTIAL" and result.get("supportingCardIds"):
        return "card_content_incomplete"
    if result.get("hitStatus") == "MISS":
        return "knowledge_missing"
    return "solution_evidence_insufficient"


def next_action(reason: str) -> str:
    if reason in {"question_boundary_missing", "question_text_incomplete", "source_evidence_missing", "question_unreadable"}:
        return "source_recovery"
    if reason == "mapping_missing":
        return "mapping_repair"
    if reason in {"card_content_incomplete", "knowledge_missing"}:
        return "knowledge_enrichment"
    if reason == "answer_provenance_conflict":
        return "solution_provenance_review"
    return "manual_review"


def build_tasks(report: dict[str, Any]) -> dict[str, Any]:
    tasks = []
    for question in report.get("questionResults", []):
        result = question.get("hitResult", {})
        if result.get("hitStatus") == "HIT":
            continue
        reason = classify(question)
        task = {
            "taskId": f"recovery-{question.get('questionId')}",
            "questionId": question.get("questionId"),
            "failureReason": reason,
            "status": "OPEN",
            "attempts": [],
            "evidenceRefs": result.get("evidenceRefs", []),
            "nextAction": next_action(reason),
            "originalHitStatus": result.get("hitStatus"),
            "cardIds": result.get("supportingCardIds", []),
        }
        tasks.append(task)
    return {
        "schemaVersion": "exam.hit.recovery.v1",
        "examHitRunId": report.get("examHitRunId"),
        "snapshot": report.get("snapshot"),
        "tasks": tasks,
        "externalSupplements": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    output = build_tasks(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tasks": len(output["tasks"]), "byReason": {reason: sum(1 for item in output["tasks"] if item["failureReason"] == reason) for reason in sorted(FAILURE_REASONS)}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
