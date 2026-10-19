"""Validate the frozen-state exam record and its state-machine invariants."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STATES = [
    "NEW_EXAM_REQUEST",
    "CLEANUP_PREVIOUS_RUN",
    "WORKSPACE_VERIFIED_CLEAN",
    "LOAD_EXAM_PDF",
    "SNAPSHOT_FROZEN",
    "FIRST_PASS",
    "ANSWERS_FROZEN",
    "SOLUTION_RELEASED",
    "GRADING",
    "POSTMORTEM",
    "CLOSED",
]
RESULTS = {"correct", "wrong", "unanswered", "partial", "blocked"}
ATTEMPT_STATUSES = {"ANSWERED", "UNANSWERED_BY_LEARNER", "BLOCKED_BY_UNREADABLE_QUESTION", "BLOCKED_BY_SOURCE", "BLOCKED_BY_GRAPH_KNOWLEDGE_GAP", "BLOCKED_BY_EXAM_SYSTEM", "PARTIAL_ANSWER"}
RETRIEVAL_RESULTS = {"FOUND", "PARTIAL_FOUND", "NOT_FOUND", "NOT_ATTEMPTED"}
ARTIFACT_STATUSES = {"OK", "DIRECT_MAPPING_MISSING", "GRAPH_KNOWLEDGE_GAP", "GRAPH_MAPPING_MISSING", "GRAPH_MAPPING_AMBIGUOUS", "SOURCE_MISSING", "SOURCE_INCOMPLETE", "ANSWER_PROVENANCE_CONFLICT", "QUESTION_UNREADABLE", "REFERENCE_ANSWER_MISSING"}
GRADING_STATUSES = {"GRADED", "UNGRADED", "BLOCKED"}
ANSWERER_TYPES = {"human", "agent", "model", "unknown"}
HIT_STATUSES = {"HIT", "PARTIAL", "MISS", "UNRESOLVED"}
PDF_READING_MODES = {"native_pdf_page_image", "native_pdf_text_and_page"}
PDF_BANNED_TOKENS = {
    "ocr",
    "tesseract",
    "pytesseract",
    "easyocr",
    "paddleocr",
    "ocrmypdf",
    "keras-ocr",
    "doctr",
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_pdf_reference(reference: Any, path: str, errors: list[str]) -> None:
    if not isinstance(reference, dict):
        errors.append(f"{path} must be an object")
        return
    if reference.get("source") != "original_pdf":
        errors.append(f"PDF_SOURCE_INTEGRITY_GATE: {path}.source must be original_pdf")
    source_path = reference.get("path")
    if not _text(source_path) or not source_path.lower().endswith(".pdf"):
        errors.append(f"PDF_SOURCE_INTEGRITY_GATE: {path}.path must point to the original PDF")
    if reference.get("readingMode") not in PDF_READING_MODES:
        errors.append(f"PDF_SOURCE_INTEGRITY_GATE: {path}.readingMode must use native PDF reading")
    if reference.get("ocrUsed") is not False:
        errors.append(f"PDF_SOURCE_INTEGRITY_GATE: {path}.ocrUsed must be false")
    if reference.get("delegatedOcr") is not False:
        errors.append(f"PDF_SOURCE_INTEGRITY_GATE: {path}.delegatedOcr must be false")
    if reference.get("intermediateTextSources") != []:
        errors.append(f"PDF_SOURCE_INTEGRITY_GATE: {path}.intermediateTextSources must be empty")


def _validate_page_reference(reference: Any, path: str, errors: list[str]) -> None:
    if not isinstance(reference, dict):
        errors.append(f"PDF_SOURCE_INTEGRITY_GATE: {path} must reference an original PDF page")
        return
    _validate_pdf_reference(
        {
            "source": reference.get("source"),
            "path": reference.get("path"),
            "readingMode": reference.get("readingMode", "native_pdf_text_and_page"),
            "ocrUsed": reference.get("ocrUsed", False),
            "delegatedOcr": reference.get("delegatedOcr", False),
            "intermediateTextSources": reference.get("intermediateTextSources", []),
        },
        path,
        errors,
    )
    if not isinstance(reference.get("page"), int) or reference["page"] < 1:
        errors.append(f"PDF_SOURCE_INTEGRITY_GATE: {path}.page must be a positive integer")


def _validate_pdf_reading(record: dict[str, Any], state_index: int, errors: list[str]) -> None:
    if state_index < STATES.index("FIRST_PASS"):
        return
    pdf_reading = record.get("pdfReading")
    if not isinstance(pdf_reading, dict):
        errors.append("PDF_SOURCE_INTEGRITY_GATE: pdfReading is required from FIRST_PASS onward")
        return
    if pdf_reading.get("sourcePolicy") != "original_pdf_only":
        errors.append("PDF_SOURCE_INTEGRITY_GATE: sourcePolicy must be original_pdf_only")
    _validate_pdf_reference(pdf_reading.get("examPdf"), "pdfReading.examPdf", errors)
    if state_index >= STATES.index("SOLUTION_RELEASED"):
        _validate_pdf_reference(pdf_reading.get("solutionPdf"), "pdfReading.solutionPdf", errors)
    for index, entry in enumerate(record.get("accessLog", [])):
        if not isinstance(entry, dict):
            continue
        combined = " ".join(str(value).lower() for value in entry.values())
        if any(token in combined for token in PDF_BANNED_TOKENS):
            errors.append(f"PDF_SOURCE_INTEGRITY_GATE: accessLog[{index}] contains a prohibited OCR path or tool")


def _validate_workspace(record: dict[str, Any], state_index: int, errors: list[str]) -> None:
    if state_index < STATES.index("CLEANUP_PREVIOUS_RUN"):
        return
    workspace = record.get("workspace")
    if not isinstance(workspace, dict):
        errors.append("EXAM_WORKSPACE_NOT_CLEAN: workspace is required before cleanup")
        return
    if workspace.get("root") != ".exam/current":
        errors.append("EXAM_WORKSPACE_NOT_CLEAN: workspace.root must be .exam/current")
    for field in ("runId", "resetAt"):
        if not _text(workspace.get(field)):
            errors.append(f"EXAM_WORKSPACE_NOT_CLEAN: workspace.{field} is required")
    if workspace.get("previousRunDeleted") is not True:
        errors.append("EXAM_WORKSPACE_NOT_CLEAN: previousRunDeleted must be true")
    residual = workspace.get("residualPaths")
    if not isinstance(residual, list):
        errors.append("EXAM_WORKSPACE_NOT_CLEAN: residualPaths must be a list")
    elif residual:
        errors.append(f"EXAM_WORKSPACE_NOT_CLEAN: residualPaths is not empty: {residual}")
    if state_index >= STATES.index("WORKSPACE_VERIFIED_CLEAN") and workspace.get("cleanVerified") is not True:
        errors.append("EXAM_WORKSPACE_NOT_CLEAN: cleanVerified must be true")
    if state_index >= STATES.index("LOAD_EXAM_PDF") and workspace.get("examLoaded") is not True:
        errors.append("EXAM_WORKSPACE_NOT_CLEAN: examLoaded must be true after LOAD_EXAM_PDF")


def _validate_execution_isolation(record: dict[str, Any], state_index: int, errors: list[str]) -> None:
    if state_index < STATES.index("FIRST_PASS"):
        return
    isolation = record.get("executionIsolation")
    if not isinstance(isolation, dict):
        errors.append("EXAM_HIT_ISOLATION: executionIsolation is required from FIRST_PASS onward")
        return
    for field in ("hitInspectorContextId", "independentAnswererContextId", "answererInputPolicy"):
        if not _text(isolation.get(field)):
            errors.append(f"EXAM_HIT_ISOLATION: executionIsolation.{field} is required")
    if isolation.get("hitInspectorContextId") == isolation.get("independentAnswererContextId"):
        errors.append("EXAM_HIT_ISOLATION: Hit Inspector and Independent Answerer contexts must differ")
    if isolation.get("phaseOrder") != ["READ_QUESTION", "EXAM_HIT", "INDEPENDENT_ANSWER", "GRADE", "FREEZE"]:
        errors.append("EXAM_HIT_ORDER: phaseOrder must be Read → Hit → Answer → Grade → Freeze")
    if isolation.get("hitCompletedBeforeAnswer") is not True or isolation.get("verified") is not True:
        errors.append("EXAM_HIT_ISOLATION: isolation and Hit-before-answer gate must be verified")
    forbidden = {"hit_analysis", "candidate_card_content", "hit_status", "missing_knowledge", "external_research", "official_answer", "official_solution"}
    if not forbidden.issubset(set(isolation.get("answererDidNotReceive", []))):
        errors.append("EXAM_HIT_ISOLATION: answererDidNotReceive must include Hit and solution data")


def _validate_question_hit(question: dict[str, Any], path: str, snapshot: dict[str, Any], isolation: dict[str, Any], errors: list[str]) -> None:
    hit = question.get("hit")
    if not isinstance(hit, dict):
        errors.append(f"EXAM_HIT_REQUIRED: {path}.hit is required before independent answer")
        return
    if hit.get("hitStatus") not in HIT_STATUSES:
        errors.append(f"EXAM_HIT_STATUS_INVALID: {path}.hit.hitStatus is invalid")
    if hit.get("graphSnapshotId") != snapshot.get("id"):
        errors.append(f"EXAM_HIT_SNAPSHOT_MISMATCH: {path}.hit.graphSnapshotId must match frozen snapshot")
    for field in ("requiredKnowledge", "supportingCardIds", "supportingContentRefs", "missingKnowledge", "hitEvidenceRefs"):
        if not isinstance(hit.get(field), list):
            errors.append(f"EXAM_HIT_EVIDENCE: {path}.hit.{field} must be a list")
    if hit.get("hitStatus") != "UNRESOLVED" and not hit.get("requiredKnowledge"):
        errors.append(f"EXAM_HIT_EVIDENCE: {path}.hit.requiredKnowledge must be non-empty")
    if hit.get("hitStatus") == "UNRESOLVED" and not _text(hit.get("unresolvedReason")):
        errors.append(f"EXAM_HIT_EVIDENCE: {path}.hit.unresolvedReason is required")
    if not _text(hit.get("hitCompletedAt")) or not _text(hit.get("inspectorContextId")):
        errors.append(f"EXAM_HIT_EVIDENCE: {path}.hit completion and inspector context are required")
    if hit.get("inspectorContextId") != isolation.get("hitInspectorContextId"):
        errors.append(f"EXAM_HIT_ISOLATION: {path}.hit inspector context mismatch")
    ref_ids: set[str] = set()
    for index, ref in enumerate(hit.get("supportingContentRefs", [])):
        ref_path = f"{path}.hit.supportingContentRefs[{index}]"
        if not isinstance(ref, dict) or not _text(ref.get("cardId")) or not _text(ref.get("field")) or not _text(ref.get("excerpt")) or not _text(ref.get("contentSha256")):
            errors.append(f"EXAM_HIT_EVIDENCE: {ref_path} must point to actual card content")
            continue
        if ref.get("field") in {"id", "title", "name", "label"}:
            errors.append(f"EXAM_HIT_EVIDENCE: {ref_path} cannot use title-only evidence")
        ref_ids.add(ref["cardId"])
    if ref_ids != set(hit.get("supportingCardIds", [])):
        errors.append(f"EXAM_HIT_EVIDENCE: {path}.hit.supportingCardIds must match content references")
    if not hit.get("hitEvidenceRefs"):
        errors.append(f"EXAM_HIT_EVIDENCE: {path}.hit.hitEvidenceRefs must be non-empty")
    if hit.get("hitStatus") == "HIT" and hit.get("missingKnowledge"):
        errors.append(f"EXAM_HIT_STATUS: {path}.HIT cannot contain missingKnowledge")
    if hit.get("hitStatus") in {"PARTIAL", "MISS"} and not hit.get("missingKnowledge"):
        errors.append(f"EXAM_HIT_STATUS: {path}.{hit.get('hitStatus')} requires missingKnowledge")


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
    answerer = record.get("answerer")
    if not isinstance(answerer, dict) or answerer.get("type") not in ANSWERER_TYPES:
        errors.append("answerer.type must be human, agent, model, or unknown")
    elif state == "CLOSED" and not _text(answerer.get("id")):
        errors.append("answerer.id is required for a CLOSED exam")
    _validate_workspace(record, state_index, errors)
    _validate_execution_isolation(record, state_index, errors)
    snapshot = record.get("snapshot")
    if not isinstance(snapshot, dict):
        errors.append("snapshot is required")
    else:
        for field in ("id", "subjectId", "artifactVersion", "frozenAt"):
            if not _text(snapshot.get(field)):
                errors.append(f"snapshot.{field} is required")
        if state_index >= STATES.index("SNAPSHOT_FROZEN") and snapshot.get("frozen") is not True:
            errors.append("snapshot.frozen must be true after SNAPSHOT_FROZEN")
        if state_index >= STATES.index("SNAPSHOT_FROZEN") and snapshot.get("migrationStatus") != "UP_TO_DATE":
            errors.append("UPDATE_REQUIRED_BEFORE_EXAM: snapshot.migrationStatus must be UP_TO_DATE")
    if record.get("updateAppliedAfterFreeze") is True:
        errors.append("UPDATE_MUTATED_FROZEN_EXAM: update cannot alter a frozen exam")
    _validate_pdf_reading(record, state_index, errors)

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
            isolation = record.get("executionIsolation", {}) if isinstance(record.get("executionIsolation"), dict) else {}
            _validate_question_hit(question, path, snapshot if isinstance(snapshot, dict) else {}, isolation, errors)
            if not isinstance(first_pass, dict):
                errors.append(f"{path}.firstPass is required from FIRST_PASS onward")
            else:
                for field in ("confidence", "reasoningSummary", "order", "attemptStatus", "retrieval"):
                    if field not in first_pass:
                        errors.append(f"{path}.firstPass.{field} is required")
                if first_pass.get("answererContextId") != isolation.get("independentAnswererContextId"):
                    errors.append(f"EXAM_HIT_ISOLATION: {path}.firstPass.answererContextId mismatch")
                if first_pass.get("answererInputPolicy") != "question_only_after_hit":
                    errors.append(f"EXAM_HIT_ISOLATION: {path}.firstPass.answererInputPolicy must be question_only_after_hit")
                if first_pass.get("phaseOrder") != ["READ_QUESTION", "EXAM_HIT", "INDEPENDENT_ANSWER"]:
                    errors.append(f"EXAM_HIT_ORDER: {path}.firstPass.phaseOrder is invalid")
                attempt_status = first_pass.get("attemptStatus")
                if attempt_status not in ATTEMPT_STATUSES:
                    errors.append(f"FIRST_PASS_STATUS_MISSING: {path}.firstPass.attemptStatus is invalid")
                retrieval = first_pass.get("retrieval")
                if not isinstance(retrieval, dict):
                    errors.append(f"{path}.firstPass.retrieval must be an object")
                else:
                    if not isinstance(retrieval.get("directMappingAvailable"), bool):
                        errors.append(f"{path}.firstPass.retrieval.directMappingAvailable must be boolean")
                    if not isinstance(retrieval.get("attempted"), bool):
                        errors.append(f"{path}.firstPass.retrieval.attempted must be boolean")
                    if retrieval.get("result") not in RETRIEVAL_RESULTS:
                        errors.append(f"{path}.firstPass.retrieval.result is invalid")
                    for field in ("candidateCardIds", "selectedCardIds", "evidence"):
                        if not isinstance(retrieval.get(field), list):
                            errors.append(f"{path}.firstPass.retrieval.{field} must be a list")
                    if record.get("executionIsolation", {}).get("answererInputPolicy") == "question_only_after_hit":
                        if retrieval.get("attempted") is not False or retrieval.get("result") != "NOT_ATTEMPTED" or any(retrieval.get(field) for field in ("queries", "candidateCardIds", "selectedCardIds", "evidence")):
                            errors.append(f"EXAM_HIT_ISOLATION: {path}.firstPass.retrieval must not expose graph retrieval to the Independent Answerer")
                    if not retrieval.get("directMappingAvailable") and retrieval.get("result") == "NOT_ATTEMPTED" and record.get("executionIsolation", {}).get("answererInputPolicy") != "question_only_after_hit" and attempt_status not in {"BLOCKED_BY_UNREADABLE_QUESTION", "BLOCKED_BY_EXAM_SYSTEM"}:
                        errors.append(f"FIRST_PASS_RETRIEVAL_NOT_ATTEMPTED: {path}")
                answer = first_pass.get("answer")
                reasoning = first_pass.get("reasoningSummary")
                if attempt_status in {"ANSWERED", "PARTIAL_ANSWER"}:
                    if not _text(answer):
                        errors.append(f"FIRST_PASS_ANSWER_MISSING: {path}.answer is required for {attempt_status}")
                    if not _text(reasoning):
                        errors.append(f"FIRST_PASS_ANSWER_MISSING: {path}.reasoningSummary is required for {attempt_status}")
                elif attempt_status == "UNANSWERED_BY_LEARNER":
                    if not _text(reasoning):
                        errors.append(f"FIRST_PASS_ANSWER_MISSING: {path}.reasoningSummary is required for unanswered learner status")
                else:
                    if not isinstance(question.get("blockerEvidence"), list) or not question["blockerEvidence"]:
                        errors.append(f"BLOCKED_WITHOUT_EVIDENCE: {path}.blockerEvidence is required")
                    if attempt_status == "BLOCKED_BY_GRAPH_KNOWLEDGE_GAP":
                        hit_status = (question.get("hit") or {}).get("hitStatus")
                        if record.get("executionIsolation", {}).get("answererInputPolicy") == "question_only_after_hit":
                            if hit_status not in {"PARTIAL", "MISS", "UNRESOLVED"}:
                                errors.append(f"GRAPH_GAP_WITHOUT_HIT: {path}")
                        elif not isinstance(retrieval, dict) or retrieval.get("attempted") is not True or retrieval.get("result") != "NOT_FOUND":
                            errors.append(f"GRAPH_GAP_WITHOUT_RETRIEVAL: {path}")
                    if attempt_status == "BLOCKED_BY_UNREADABLE_QUESTION" and isinstance(retrieval, dict) and retrieval.get("attempted") is True:
                        errors.append(f"UNREADABLE_QUESTION_RETRIEVAL_MISMATCH: {path}")
        if state_index >= STATES.index("ANSWERS_FROZEN") and question.get("firstPassFrozen") is not True:
            errors.append(f"{path}.firstPassFrozen must be true after ANSWERS_FROZEN")
        if state_index >= STATES.index("FIRST_PASS"):
            _validate_page_reference(question.get("examPage"), f"{path}.examPage", errors)
        grading = question.get("grading")
        if state_index >= STATES.index("GRADING"):
            if not isinstance(grading, dict):
                errors.append(f"{path}.grading is required from GRADING onward")
            else:
                if grading.get("result") not in RESULTS:
                    errors.append(f"{path}.grading.result is invalid")
                if grading.get("gradingStatus") not in GRADING_STATUSES:
                    errors.append(f"{path}.grading.gradingStatus is invalid")
                attempt_status = first_pass.get("attemptStatus") if isinstance(first_pass, dict) else None
                if attempt_status in {"BLOCKED_BY_SOURCE", "BLOCKED_BY_GRAPH_KNOWLEDGE_GAP", "BLOCKED_BY_UNREADABLE_QUESTION", "BLOCKED_BY_EXAM_SYSTEM"} and grading.get("result") != "blocked":
                    errors.append(f"GRADING_ATTEMPT_STATUS_MISMATCH: {path} blocked attempt must have blocked grading")
                if attempt_status == "UNANSWERED_BY_LEARNER" and grading.get("result") != "unanswered":
                    errors.append(f"UNANSWERED_STATUS_MISMATCH: {path}")
                if attempt_status in {"ANSWERED", "PARTIAL_ANSWER"} and grading.get("result") == "blocked":
                    errors.append(f"GRADING_ATTEMPT_STATUS_MISMATCH: {path}")
        artifact_status = question.get("artifactStatus", "OK")
        if artifact_status not in ARTIFACT_STATUSES:
            errors.append(f"{path}.artifactStatus is invalid")
        revisions = question.get("revisions", [])
        if not isinstance(revisions, list):
            errors.append(f"{path}.revisions must be a list")
        official = question.get("official")
        if state_index >= STATES.index("SOLUTION_RELEASED") and isinstance(official, dict):
            _validate_page_reference(official.get("sourcePage"), f"{path}.official.sourcePage", errors)

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
            if phase == "FIRST_PASS" and source in {"web", "solution", "answer_key", "unfrozen_subject", "ocr", "ocr_text", "transcript"}:
                errors.append(f"accessLog[{index}] violates FIRST_PASS access policy")

    for field in ("officialAnswersReleasedAt", "gradingCompletedAt", "closedAt"):
        if field in record and record[field] is not None and not _text(record[field]):
            errors.append(f"{field} must be a timestamp string or null")
    if state_index >= STATES.index("SOLUTION_RELEASED") and not _text(record.get("officialAnswersReleasedAt")):
        errors.append("officialAnswersReleasedAt is required after SOLUTION_RELEASED")
    if state_index >= STATES.index("ANSWERS_FROZEN"):
        coverage = record.get("firstPassCoverage")
        if not isinstance(coverage, dict):
            errors.append("FIRST_PASS_COVERAGE_INCOMPLETE: firstPassCoverage is required before answers freeze")
        else:
            fields = ("totalQuestions", "processedQuestions", "answered", "unansweredByLearner", "blocked", "unprocessed")
            if any(not isinstance(coverage.get(field), int) or isinstance(coverage.get(field), bool) or coverage.get(field) < 0 for field in fields):
                errors.append("FIRST_PASS_COVERAGE_COUNT_MISMATCH: coverage counts must be non-negative integers")
            elif coverage["totalQuestions"] != len(questions) or coverage["processedQuestions"] != coverage["totalQuestions"] or coverage["unprocessed"] != 0:
                errors.append("FIRST_PASS_COVERAGE_INCOMPLETE: every question must have a processing status")
            elif coverage["totalQuestions"] != coverage["answered"] + coverage["unansweredByLearner"] + coverage["blocked"]:
                errors.append("FIRST_PASS_COVERAGE_COUNT_MISMATCH: status counts do not sum to total")
            if coverage.get("complete") is not True:
                errors.append("FIRST_PASS_COVERAGE_INCOMPLETE: complete must be true before answers freeze")

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
            if request.get("owner") not in {"review", "learn", "study-math", "study-politics", "study-exam-oriented-english", "domain-model", "check", "fix", "heal", "amend"}:
                errors.append(f"REPAIR_REQUEST_OWNER_INVALID: repairRequests[{index}].owner is not supported")
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
