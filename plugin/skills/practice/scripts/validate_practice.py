"""Validate generated practice PDFs and their stable manifest/record boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _pdf_text(path: Path) -> str:
    executable = shutil.which("pdftotext")
    if not executable:
        return ""
    result = subprocess.run([executable, str(path), "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.stdout


def _pdf_pages(path: Path) -> int | None:
    executable = shutil.which("pdfinfo")
    if not executable:
        return None
    result = subprocess.run([executable, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def validate_practice(manifest: Any, record: Any, questions_pdf: Path, answers_pdf: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != "practice-manifest.v1":
        errors.append("manifest schemaVersion must be practice-manifest.v1")
        return errors
    if not isinstance(record, dict) or record.get("schemaVersion") != "practice-record.v1":
        errors.append("record schemaVersion must be practice-record.v1")
    question_entries = manifest.get("questions")
    if not isinstance(question_entries, list) or not question_entries:
        errors.append("manifest.questions must be non-empty")
        question_entries = []
    ids = [item.get("questionId") for item in question_entries if isinstance(item, dict)]
    if len(ids) != len(set(ids)) or any(not isinstance(value, str) or not value for value in ids):
        errors.append("question IDs must be unique and non-empty")
    numbers = [item.get("number") for item in question_entries if isinstance(item, dict)]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append("question numbers must be continuous")
    for path in (questions_pdf, answers_pdf):
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty PDF: {path}")
        elif _pdf_pages(path) == 0:
            errors.append(f"PDF has no pages: {path}")
    if questions_pdf.is_file():
        expected = manifest.get("questionPdf", {})
        if expected.get("sha256") != _sha256(questions_pdf):
            errors.append("questions.pdf hash does not match manifest")
        question_text = _pdf_text(questions_pdf)
        if question_text.strip():
            if "答案与解析" in question_text or "标准答案" in question_text:
                errors.append("questions.pdf exposes answer headings")
            for question_id in ids:
                if question_id not in question_text:
                    errors.append(f"questions.pdf is missing question ID {question_id}")
    if answers_pdf.is_file():
        expected = manifest.get("answerPdf", {})
        if expected.get("sha256") != _sha256(answers_pdf):
            errors.append("answers.pdf hash does not match manifest")
        answer_text = _pdf_text(answers_pdf)
        if answer_text.strip():
            for question_id in ids:
                if question_id not in answer_text and str(next((item.get("number") for item in question_entries if item.get("questionId") == question_id), "")) not in answer_text:
                    errors.append(f"answers.pdf is missing question {question_id}")
    if isinstance(record, dict):
        if record.get("state") != "READY_FOR_ATTEMPT":
            errors.append("practice record must start READY_FOR_ATTEMPT")
        if record.get("answerReleased") is not False:
            errors.append("answers must remain unreleased before submission")
        if not isinstance(record.get("attempts"), list):
            errors.append("record.attempts must be a list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate practice PDFs and records.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--questions-pdf", type=Path, required=True)
    parser.add_argument("--answers-pdf", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        record = json.loads(args.record.read_text(encoding="utf-8"))
        errors = validate_practice(manifest, record, args.questions_pdf, args.answers_pdf)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print("PASS: validated practice PDFs and records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
