"""Validate an evidence-based Exam Result review report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_annotations import validate_overlay


OUTCOMES = {"correct", "incorrect", "partially_correct", "unanswered", "unreadable", "ungraded", "invalid"}
STAGES = {"RETRIEVAL", "METHOD_SELECTION", "CONDITION_CHECK", "SETUP", "EXECUTION", "VERIFICATION", "EXPRESSION", "READING", "MEMORY", "TIME", "SOURCE_ISSUE"}
ERRORS = {"CONCEPT_MISUNDERSTANDING", "KNOWLEDGE_MISSING", "CONDITION_MISSED", "METHOD_SELECTION_ERROR", "REASONING_ERROR", "EXECUTION_ERROR", "READING_ERROR", "CONNECTION_GAP", "MEMORY_FAILURE", "UNKNOWN"}
DIAGNOSTIC_STATUSES = {"confirmed", "hypothesis", "unknown", "blocked"}
MASTERY_STATUSES = {"unknown", "needs_diagnosis", "weak", "developing", "proficient", "verified"}
ROUTES = {"learner_model", "amend", "check", "fix", "heal", "none"}
COMPLETENESS = {"COMPLETE", "PARTIAL", "UNKNOWN", "BLOCKED", "NOT_APPLIED"}
REPORT_STATUSES = {"COMPLETE", "PARTIAL", "BLOCKED", "FAILED"}
ANSWERER_TYPES = {"human", "agent", "model", "unknown"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _confidence(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1


def _evidence(value: Any, path: str, required: bool = True) -> list[str]:
    if not isinstance(value, list) or (required and not value) or any(not _text(item) for item in value):
        return [f"{path} must contain evidence references"]
    return []


def _mastery_assessment(value: Any, path: str, question: bool) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    id_field = "questionId" if question else "cardId"
    if not _text(value.get(id_field)):
        errors.append(f"{path}.{id_field} must be non-empty")
    for field in ("previousStatus", "newStatus"):
        if value.get(field) not in MASTERY_STATUSES:
            errors.append(f"{path}.{field} is invalid")
    errors.extend(_evidence(value.get("evidenceRefs"), f"{path}.evidenceRefs"))
    if not _text(value.get("assessmentReason")):
        errors.append(f"{path}.assessmentReason must be non-empty")
    if value.get("newStatus") == "verified" and not value.get("independentEvidence"):
        errors.append(f"{path}.independentEvidence must be true for verified")
    return errors


def validate_report(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") != "review.report.v2":
        errors.append("schemaVersion must be review.report.v2")
    if not _text(report.get("reviewRunId")) or not _text(report.get("diagnosticVersion")):
        errors.append("reviewRunId and diagnosticVersion must be non-empty")
    if report.get("status") not in REPORT_STATUSES:
        errors.append("status is invalid")
    if report.get("source") != "exam_result":
        errors.append("source must be exam_result")

    exam = report.get("exam")
    if not isinstance(exam, dict):
        errors.append("exam is required")
    else:
        for field in ("examRunId", "subjectId", "artifactVersion", "artifactHash", "resultPath", "examResultHashBefore", "examResultHashAfter", "answererType"):
            if not _text(exam.get(field)):
                errors.append(f"exam.{field} must be non-empty")
        if exam.get("status") != "CLOSED":
            errors.append("REVIEW_INPUT_NOT_CLOSED: exam.status must be CLOSED")
        if exam.get("answersFrozen") is not True:
            errors.append("exam.answersFrozen must be true")
        if exam.get("attemptsImmutable") is not True:
            errors.append("exam.attemptsImmutable must be true")
        if exam.get("answererType") not in ANSWERER_TYPES:
            errors.append("exam.answererType is invalid")
        if exam.get("examResultHashBefore") != exam.get("examResultHashAfter"):
            errors.append("REVIEW_MUTATED_EXAM_RESULT: exam result hash changed")

    scope = report.get("reviewScope")
    if not isinstance(scope, dict):
        errors.append("reviewScope is required")
    else:
        if scope.get("readPdf") is not True:
            errors.append("REVIEW_SCOPE_VIOLATION: readPdf must be true")
        for field in ("reanswered", "regraded", "remappedGraph", "auditedArtifact", "mutatedArtifact"):
            if scope.get(field) is not False:
                errors.append(f"REVIEW_SCOPE_VIOLATION: {field} must be false")

    eligibility = report.get("reviewEligibility")
    if not isinstance(eligibility, dict) or any(not _non_negative_int(eligibility.get(field)) for field in ("eligible", "artifactBlocked", "gradingBlocked", "conflicted")):
        errors.append("reviewEligibility is incomplete")

    annotations = report.get("annotations")
    if not isinstance(annotations, list):
        errors.append("annotations must be a list")
    else:
        overlay_errors = validate_overlay({"schemaVersion": "review.annotation-overlay.v1", "subjectId": exam.get("subjectId") if isinstance(exam, dict) else "", "reviewRunId": report.get("reviewRunId"), "annotations": annotations})
        errors.extend(f"annotation: {error}" for error in overlay_errors)

    completeness = report.get("completeness")
    if not isinstance(completeness, dict):
        errors.append("completeness is required")
    else:
        for field in ("examCompleteness", "gradingCompleteness", "diagnosticCompleteness", "mappingCompleteness", "masteryUpdateStatus", "reviewStatus"):
            if completeness.get(field) not in COMPLETENESS:
                errors.append(f"completeness.{field} is invalid")
        counts = completeness.get("counts")
        if not isinstance(counts, dict) or any(not _non_negative_int(counts.get(field)) for field in ("total", "attempted", "scored", "ungraded", "unanswered", "unreadable", "invalid")):
            errors.append("completeness.counts is incomplete")
        elif counts["attempted"] > counts["total"] or counts["scored"] > counts["attempted"]:
            errors.append("completeness counts have impossible denominators")

    questions = report.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append("questions must be a non-empty list")
        questions = []
    for index, item in enumerate(questions):
        path = f"questions[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("questionId", "attemptId"):
            if not _text(item.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        outcome = item.get("observedOutcome")
        if outcome not in OUTCOMES:
            errors.append(f"{path}.observedOutcome is invalid")
        if item.get("attemptStatus") not in {"ANSWERED", "UNANSWERED_BY_LEARNER", "NOT_ATTEMPTED", "BLOCKED_BY_SOURCE", "BLOCKED_BY_MAPPING", "SKIPPED_BY_EXAM"}:
            errors.append(f"{path}.attemptStatus is invalid")
        if item.get("gradingStatus") not in {"GRADED", "UNGRADED", "BLOCKED"}:
            errors.append(f"{path}.gradingStatus is invalid")
        if item.get("artifactStatus") not in {"OK", "GRAPH_MAPPING_MISSING", "GRAPH_MAPPING_AMBIGUOUS", "SOURCE_MISSING", "SOURCE_INCOMPLETE", "ANSWER_PROVENANCE_CONFLICT", "QUESTION_UNREADABLE", "REFERENCE_ANSWER_MISSING"}:
            errors.append(f"{path}.artifactStatus is invalid")
        if not isinstance(item.get("learnerAttributionEligible"), bool):
            errors.append(f"{path}.learnerAttributionEligible must be boolean")
        gate_blocked = item.get("gradingStatus") != "GRADED" or item.get("artifactStatus") != "OK" or item.get("attemptStatus") not in {"ANSWERED", "UNANSWERED_BY_LEARNER"}
        if item.get("learnerAttributionEligible") and gate_blocked:
            errors.append(f"{path}.LEARNER_ATTRIBUTION_GATE violated")
        if item.get("learnerAttributionEligible") and item.get("answerConflict") is True:
            errors.append(f"{path}.conflicted question cannot be learner-attribution eligible")
        links = item.get("knowledgeLinks")
        if not isinstance(links, dict) or not _text(links.get("primaryCardId")) or not isinstance(links.get("secondaryCardIds"), list) or not isinstance(links.get("relationIds"), list):
            errors.append(f"{path}.knowledgeLinks is incomplete")
        diagnosis = item.get("diagnosis")
        if not isinstance(diagnosis, dict):
            errors.append(f"{path}.diagnosis is required")
        else:
            if diagnosis.get("errorCategory") not in ERRORS:
                errors.append(f"{path}.diagnosis.errorCategory is invalid")
            if diagnosis.get("errorStep") is not None and diagnosis.get("errorStep") not in STAGES:
                errors.append(f"{path}.diagnosis.errorStep is invalid")
            if diagnosis.get("evidenceLevel") not in {"full_process", "final_answer_only", "metadata_only"}:
                errors.append(f"{path}.diagnosis.evidenceLevel is invalid")
            if diagnosis.get("evidenceLevel") != "full_process" and diagnosis.get("errorStep") is not None:
                errors.append(f"{path}.diagnosis.errorStep cannot be inferred without a full process")
            if diagnosis.get("diagnosticStatus") not in DIAGNOSTIC_STATUSES:
                errors.append(f"{path}.diagnosis.diagnosticStatus is invalid")
            if not _confidence(diagnosis.get("confidence")):
                errors.append(f"{path}.diagnosis.confidence is invalid")
            errors.extend(_evidence(diagnosis.get("evidenceRefs"), f"{path}.diagnosis.evidenceRefs"))
            if not isinstance(diagnosis.get("hypotheses"), list):
                errors.append(f"{path}.diagnosis.hypotheses must be a list")
            else:
                for hypothesis in diagnosis["hypotheses"]:
                    if not isinstance(hypothesis, dict) or not _text(hypothesis.get("code")) or not _text(hypothesis.get("reason")) or not _confidence(hypothesis.get("confidence")):
                        errors.append(f"{path}.diagnosis.hypotheses contains an invalid hypothesis")
            if diagnosis.get("diagnosticStatus") == "confirmed" and diagnosis.get("errorCategory") == "UNKNOWN":
                errors.append(f"{path}.confirmed diagnosis cannot use UNKNOWN")
            if outcome in {"unanswered", "unreadable", "ungraded", "invalid"} and diagnosis.get("diagnosticStatus") == "confirmed":
                errors.append(f"{path}.incomplete outcome cannot have confirmed learner diagnosis")
        knowledge_mastery = item.get("knowledgeMastery")
        if not isinstance(knowledge_mastery, list) or not knowledge_mastery:
            errors.append(f"{path}.knowledgeMastery must be a non-empty list")
        else:
            for mastery_index, assessment in enumerate(knowledge_mastery):
                errors.extend(_mastery_assessment(assessment, f"{path}.knowledgeMastery[{mastery_index}]", False))
        errors.extend(_mastery_assessment(item.get("questionMastery"), f"{path}.questionMastery", True) if isinstance(item.get("questionMastery"), dict) else [f"{path}.questionMastery must be an object"])
        update = item.get("learnerModelUpdate")
        if not isinstance(update, dict) or not isinstance(update.get("observation"), bool) or not _text(update.get("idempotencyKey")):
            errors.append(f"{path}.learnerModelUpdate is incomplete")
        elif update.get("observation") and not item.get("learnerAttributionEligible"):
            errors.append(f"LEARNER_UPDATE_FROM_BLOCKED_QUESTION: {path}")
        elif update.get("observation") and (not isinstance(exam, dict) or exam.get("answererType") != "human"):
            errors.append(f"LEARNER_UPDATE_FROM_NON_HUMAN: {path}")
        if item.get("route") not in ROUTES:
            errors.append(f"{path}.route is invalid")

    tasks = report.get("learningTasks")
    if not isinstance(tasks, list):
        errors.append("learningTasks must be a list")
    else:
        for index, task in enumerate(tasks):
            path = f"learningTasks[{index}]"
            if not isinstance(task, dict):
                errors.append(f"{path} must be an object")
                continue
            for field in ("taskId", "why", "problem", "operation", "acceptanceCriteria", "status"):
                if not _text(task.get(field)):
                    errors.append(f"{path}.{field} must be non-empty")
            for field in ("targetCardIds", "targetQuestionIds", "dependsOnCardIds", "evidenceRefs"):
                if not isinstance(task.get(field), list):
                    errors.append(f"{path}.{field} must be a list")

    retests = report.get("retestPlans")
    if not isinstance(retests, list):
        errors.append("retestPlans must be a list")
    else:
        for index, plan in enumerate(retests):
            path = f"retestPlans[{index}]"
            if not isinstance(plan, dict):
                errors.append(f"{path} must be an object")
                continue
            for field in ("planId", "testMethod", "successCriteria", "verificationStatus"):
                if not _text(plan.get(field)):
                    errors.append(f"{path}.{field} must be non-empty")
            for field in ("targetCardIds", "targetOperations", "evidenceRequirements"):
                if not isinstance(plan.get(field), list) or not plan[field]:
                    errors.append(f"{path}.{field} must be non-empty")
            if plan.get("verificationStatus") == "verified":
                errors.append(f"{path} cannot start as verified")
            if plan.get("independentAttemptRequired") is not True or plan.get("replayOfAttemptAllowed") is not False:
                errors.append(f"{path} must require independent non-replay evidence")

    history = report.get("historicalProgress")
    if not isinstance(history, dict) or not _text(history.get("comparisonStatus")) or not _text(history.get("conclusion")) or not isinstance(history.get("comparisons"), list):
        errors.append("historicalProgress is incomplete")

    model = report.get("learnerModel")
    if not isinstance(model, dict) or not _non_negative_int(model.get("observationsAppended")) or model.get("historicalObservationsPreserved") is not True or not isinstance(model.get("idempotencyKeys"), list) or not isinstance(model.get("updatedPaths"), list):
        errors.append("learnerModel is incomplete")
    for field in ("routing", "localValidation"):
        if not isinstance(report.get(field), dict):
            errors.append(f"{field} is required")
    validation = report.get("localValidation")
    if isinstance(validation, dict) and validation.get("status") not in {"PASS", "FAIL"}:
        errors.append("localValidation.status must be PASS or FAIL")
    for field in ("examResultMutation", "artifactMutation", "profileSelfReportMutation"):
        if report.get(field) is not False:
            errors.append(f"{field} must be false")
    if not isinstance(report.get("nextActions"), list):
        errors.append("nextActions must be a list")
    if report.get("fullCheckRun") is not None:
        errors.append("fullCheckRun must be null; review does not run full check")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an evidence-based review report.")
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
