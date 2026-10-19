"""Validate a question-by-question exam-hit report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STATUSES = {"HIT", "PARTIAL", "MISS", "UNRESOLVED"}
FAILURE_REASONS = {
    "question_boundary_missing", "question_text_incomplete", "source_evidence_missing", "question_unreadable",
    "mapping_missing", "card_content_incomplete", "knowledge_missing", "solution_evidence_insufficient",
    "answer_provenance_conflict",
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_report(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") != "exam.hit.report.v1":
        errors.append("schemaVersion must be exam.hit.report.v1")
    for field in ("examHitRunId", "examId", "subjectId"):
        if not _text(report.get(field)):
            errors.append(f"{field} must be non-empty")
    if report.get("auditStatus") not in {"COMPLETE", "PARTIAL"}:
        errors.append("auditStatus is invalid")
    if report.get("selectionPolicy") != "all_questions":
        errors.append("selectionPolicy must be all_questions")
    if report.get("generatedFromAllQuestions") is not True or report.get("preselectedFocusUsed") is not False:
        errors.append("report must be generated from all questions without preselected focus")
    for field in ("sourceMutation", "examResultMutation", "learnerModelMutation", "snapshotMutated"):
        if report.get(field) is not False:
            errors.append(f"{field} must be false")
    snapshot = report.get("snapshot")
    if not isinstance(snapshot, dict):
        errors.append("snapshot is required")
    else:
        for field in ("snapshotId", "artifactVersion", "contentSha256", "frozenAt"):
            if not _text(snapshot.get(field)):
                errors.append(f"snapshot.{field} must be non-empty")
        if snapshot.get("frozen") is not True or snapshot.get("readOnly") is not True:
            errors.append("snapshot must remain frozen and read-only")
    questions = report.get("questionResults")
    if not isinstance(questions, list) or not questions:
        errors.append("questionResults must be a non-empty list")
        questions = []
    ids: set[str] = set()
    counts = {status: 0 for status in STATUSES}
    card_ids_from_hits: set[str] = set()
    for index, question in enumerate(questions):
        path = f"questionResults[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{path} must be an object")
            continue
        qid = question.get("questionId")
        if not _text(qid):
            errors.append(f"{path}.questionId must be non-empty")
        elif qid in ids:
            errors.append(f"{path}.questionId is duplicated")
        else:
            ids.add(qid)
        if not isinstance(question.get("requiredKnowledge"), list):
            errors.append(f"{path}.requiredKnowledge must be a list")
        result = question.get("hitResult")
        if not isinstance(result, dict):
            errors.append(f"{path}.hitResult is required")
            continue
        status = result.get("hitStatus")
        if status not in STATUSES:
            errors.append(f"{path}.hitResult.hitStatus is invalid")
            continue
        counts[status] += 1
        refs = result.get("supportingCardContentRefs")
        if not isinstance(refs, list):
            errors.append(f"{path}.hitResult.supportingCardContentRefs must be a list")
            refs = []
        ref_ids: set[str] = set()
        for ref_index, ref in enumerate(refs):
            ref_path = f"{path}.hitResult.supportingCardContentRefs[{ref_index}]"
            if not isinstance(ref, dict):
                errors.append(f"{ref_path} must be an object")
                continue
            if not _text(ref.get("cardId")) or not _text(ref.get("field")) or not _text(ref.get("excerpt")) or not _text(ref.get("contentSha256")):
                errors.append(f"{ref_path} must include cardId, field, excerpt, and contentSha256")
            if ref.get("field") in {"id", "title", "name", "label"}:
                errors.append(f"{ref_path} cannot use title-only evidence")
            if _text(ref.get("cardId")):
                ref_ids.add(ref["cardId"])
        if set(result.get("supportingCardIds", [])) != ref_ids:
            errors.append(f"{path}.supportingCardIds must match supportingCardContentRefs")
        if not isinstance(result.get("evidenceRefs"), list) or not result["evidenceRefs"]:
            errors.append(f"{path}.hitResult.evidenceRefs must be non-empty")
        if status != "UNRESOLVED" and not _text(result.get("supportedReasoning")):
            errors.append(f"{path}.hitResult.supportedReasoning must be non-empty")
        if status == "UNRESOLVED" and not _text(result.get("unresolvedReason")):
            errors.append(f"{path}.hitResult.unresolvedReason is required")
        failure_reason = result.get("failureReason")
        if failure_reason is not None and failure_reason not in FAILURE_REASONS:
            errors.append(f"{path}.hitResult.failureReason is invalid")
        if status == "UNRESOLVED" and failure_reason is None:
            errors.append(f"{path}.hitResult.failureReason is required for UNRESOLVED")
        missing = result.get("missingKnowledge")
        if status in {"PARTIAL", "MISS"} and (not isinstance(missing, list) or not missing):
            errors.append(f"{path}.missingKnowledge is required for {status}")
        if status == "HIT" and missing not in (None, []):
            errors.append(f"{path}.HIT cannot have missingKnowledge")
        confidence = result.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            errors.append(f"{path}.confidence must be between 0 and 1")
        if status == "HIT":
            card_ids_from_hits.update(ref_ids)
    summary = report.get("coverageSummary")
    if not isinstance(summary, dict):
        errors.append("coverageSummary is required")
    else:
        if summary.get("totalQuestions") != len(questions):
            errors.append("coverageSummary.totalQuestions must equal questionResults length")
        if summary.get("counts") != counts:
            errors.append("coverageSummary.counts must be recomputed from every question")
        determinate = len(questions) - counts["UNRESOLVED"]
        expected_complete = counts["HIT"] / len(questions) if questions else 0
        expected_determinate = counts["HIT"] / determinate if determinate else None
        if summary.get("determinateQuestions") != determinate:
            errors.append("coverageSummary.determinateQuestions is incorrect")
        if summary.get("completeCoverageRate") != expected_complete:
            errors.append("coverageSummary.completeCoverageRate is incorrect")
        if summary.get("determinateCoverageRate") != expected_determinate:
            errors.append("coverageSummary.determinateCoverageRate is incorrect")
        focus = summary.get("derivedFocusFromObservedHits")
        if not isinstance(focus, list) or any(card_id not in card_ids_from_hits for card_id in focus):
            errors.append("derived focus must come only from observed supporting card hits")
        if isinstance(focus, list) and set(focus) != set(card_ids_from_hits if counts["HIT"] else set()):
            errors.append("derived focus cannot include cards without a HIT")
    if report.get("auditStatus") == "COMPLETE" and counts["UNRESOLVED"]:
        errors.append("COMPLETE audit cannot contain UNRESOLVED questions")
    if report.get("auditStatus") == "PARTIAL" and not counts["UNRESOLVED"]:
        errors.append("PARTIAL audit requires at least one UNRESOLVED question")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a question-by-question exam-hit report.")
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
    print("PASS: validated exam-hit coverage report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
