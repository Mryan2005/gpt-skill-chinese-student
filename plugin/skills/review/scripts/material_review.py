"""Build a material-focused review from a closed Exam Result.

This module never infers learner weakness and never mutates the Exam Result.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


BLOCKER_CODES = {
    "GRAPH_MAPPING_MISSING": "check",
    "GRAPH_MAPPING_AMBIGUOUS": "check",
    "SOURCE_MISSING": "check",
    "SOURCE_INCOMPLETE": "check",
    "ANSWER_PROVENANCE_CONFLICT": "amend",
    "QUESTION_UNREADABLE": "check",
    "REFERENCE_ANSWER_MISSING": "amend",
}


def _cards(question: dict[str, Any]) -> list[str]:
    values: list[str] = []
    values.extend(value for value in question.get("knowledgeCardsUsed", []) if isinstance(value, str))
    values.extend(value for value in question.get("selectedCardIds", []) if isinstance(value, str))
    values.extend(value for value in question.get("expectedCards", []) if isinstance(value, str))
    first_pass = question.get("firstPass", {})
    for key in ("knowledgeCardsUsed",):
        values.extend(value for value in first_pass.get(key, []) if isinstance(value, str))
    retrieval = first_pass.get("retrieval", {})
    values.extend(value for value in retrieval.get("selectedCardIds", []) if isinstance(value, str))
    values.extend(value for value in question.get("expectedCards", []) if isinstance(value, str))
    return sorted(set(values))


def build_material_review(exam_result: dict[str, Any], review_run_id: str) -> dict[str, Any]:
    questions = exam_result.get("questions", [])
    answerer = exam_result.get("answerer", {})
    answerer_type = answerer.get("type", "unknown") if isinstance(answerer, dict) else "unknown"
    annotations: list[dict[str, Any]] = []
    blocker_by_code: dict[str, set[str]] = defaultdict(set)
    card_questions: dict[str, set[str]] = defaultdict(set)
    counts = Counter()

    for question in questions:
        question_id = question.get("questionId", "unknown-question")
        counts[question.get("attemptStatus", "UNKNOWN").lower()] += 1
        grading = question.get("grading", {})
        if isinstance(grading, dict):
            counts[f"grading:{grading.get('result', 'unknown')}"] += 1
        blocker = question.get("artifactStatus")
        if blocker and blocker != "OK":
            blocker_by_code[blocker].add(question_id)
        cards = _cards(question)
        for card_id in cards:
            card_questions[card_id].add(question_id)
        if question.get("artifactStatus") == "ANSWER_PROVENANCE_CONFLICT":
            route = "amend"
        elif question.get("artifactStatus") and question.get("artifactStatus") != "OK":
            route = BLOCKER_CODES.get(question["artifactStatus"], "check")
        else:
            route = "material"
        grading_result = question.get("grading", {}).get("result") if isinstance(question.get("grading"), dict) else None
        if cards or grading_result in {"wrong", "partial"} or question.get("correct") is False:
            evidence = [f"{question_id}.examPage", f"{question_id}.grading"]
            annotations.append({
                "highlightId": f"material-{review_run_id}-{question_id}",
                "subjectId": exam_result.get("subjectId", "unknown"),
                "reviewRunId": review_run_id,
                "targetType": "question",
                "targetId": question_id,
                "highlightType": "must_practice" if route == "material" else "key_source_span",
                "priority": "high" if route == "material" else "medium",
                "evidenceStrength": "supported" if question.get("grading", {}).get("result") in {"correct", "wrong", "partial"} else "tentative",
                "reason": "Material review identified a question-level study target from the closed Exam Result.",
                "evidenceRefs": evidence,
                "labels": ["material-review"],
                "actionHint": "Read the reliable question and explanation evidence, then route the target to learn or the blocker owner.",
                "renderHint": "highlight",
                "status": "active",
                "anchor": {"status": "resolved", "locator": f"question:{question_id}"},
                "route": route,
            })

    for card_id, question_ids in sorted(card_questions.items()):
        annotations.append({
            "highlightId": f"material-{review_run_id}-{card_id}",
            "subjectId": exam_result.get("subjectId", "unknown"),
            "reviewRunId": review_run_id,
            "targetType": "card",
            "targetId": card_id,
            "highlightType": "must_practice",
            "priority": "high" if len(question_ids) > 1 else "medium",
            "evidenceStrength": "supported",
            "reason": "This card is referenced by reliable exam question evidence.",
            "evidenceRefs": sorted(f"question:{question_id}" for question_id in question_ids),
            "labels": ["material-review", "exam-linked"],
            "actionHint": "Open the card and review the linked questions.",
            "renderHint": "highlight",
            "status": "active",
            "anchor": {"status": "resolved", "locator": f"card:{card_id}"},
        })

    blocker_summary = [
        {"code": code, "questionCount": len(ids), "questionIds": sorted(ids), "route": BLOCKER_CODES.get(code, "check")}
        for code, ids in sorted(blocker_by_code.items())
    ]
    study_lines = [
        f"# Material Review: {exam_result.get('subjectId', 'unknown')}",
        "",
        f"Answerer type: `{answerer_type}`. This material review does not update the user's Learner Model.",
        "",
        "## Review focus",
        "",
    ]
    if not annotations:
        study_lines.append("No evidence-backed material focus could be generated from this Exam Result.")
    for annotation in annotations:
        study_lines.extend([
            f"### {annotation['targetId']}",
            f"- Type: `{annotation['highlightType']}`",
            f"- Priority: `{annotation['priority']}`",
            f"- Reason: {annotation['reason']}",
            f"- Evidence: {', '.join(annotation['evidenceRefs'])}",
            f"- Action: {annotation['actionHint']}",
            "",
        ])
    study_lines.extend(["## Blockers and routes", ""])
    if blocker_summary:
        for blocker in blocker_summary:
            study_lines.append(f"- `{blocker['code']}`: {blocker['questionCount']} question(s) → `{blocker['route']}`")
    else:
        study_lines.append("- No Exam-reported material blockers.")

    return {
        "schemaVersion": "material-review.report.v1",
        "reviewRunId": review_run_id,
        "examRunId": exam_result.get("examRunId"),
        "subjectId": exam_result.get("subjectId"),
        "answererType": answerer_type,
        "learnerModelWriteAllowed": answerer_type == "human",
        "counts": dict(counts),
        "blockers": blocker_summary,
        "annotations": annotations,
        "studyGuideMarkdown": "\n".join(study_lines),
        "routes": sorted(set(item["route"] for item in annotations if item.get("route") not in {"material", None})),
        "examResultMutation": False,
    }
