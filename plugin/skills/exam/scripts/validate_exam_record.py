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
RESULTS = {"correct", "wrong", "unanswered", "partial"}
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
    _validate_workspace(record, state_index, errors)
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
            if not isinstance(first_pass, dict):
                errors.append(f"{path}.firstPass is required from FIRST_PASS onward")
            else:
                for field in ("answer", "confidence", "reasoningSummary", "order"):
                    if field not in first_pass:
                        errors.append(f"{path}.firstPass.{field} is required")
        if state_index >= STATES.index("ANSWERS_FROZEN") and question.get("firstPassFrozen") is not True:
            errors.append(f"{path}.firstPassFrozen must be true after ANSWERS_FROZEN")
        if state_index >= STATES.index("FIRST_PASS"):
            _validate_page_reference(question.get("examPage"), f"{path}.examPage", errors)
        grading = question.get("grading")
        if state_index >= STATES.index("GRADING"):
            if not isinstance(grading, dict):
                errors.append(f"{path}.grading is required from GRADING onward")
            elif grading.get("result") not in RESULTS:
                errors.append(f"{path}.grading.result is invalid")
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
