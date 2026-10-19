"""Create a review-input.v2 routing manifest for exam-result or user-written mode."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _source(path: Path, role: str) -> dict[str, Any]:
    return {"role": role, "path": str(path), "sha256": _hash(path), "source": "original_pdf", "readingMode": "native_pdf_page_or_text", "ocrUsed": False, "delegatedOcr": False, "intermediateTextSources": []}


def route_review(mode: str | None, *, exam_result: Path | None, questions_pdf: Path | None, answers_pdf: Path | None, submission_pdf: Path | None, attempt_id: str | None, review_run_id: str) -> dict[str, Any]:
    selected = mode or "exam-result"
    if selected not in {"exam-result", "user-written"}:
        raise ValueError("mode must be exam-result or user-written")
    if selected == "exam-result":
        if exam_result is None or not exam_result.is_file():
            raise ValueError("exam-result mode requires --exam-result")
        record = json.loads(exam_result.read_text(encoding="utf-8"))
        answerer = record.get("answerer", {}) if isinstance(record, dict) else {}
        answerer_type = answerer.get("type", "unknown") if isinstance(answerer, dict) else "unknown"
        return {
            "schemaVersion": "review-input.v2",
            "reviewMode": "exam-result",
            "reviewRunId": review_run_id,
            "examRunId": record.get("examId") or record.get("examRunId"),
            "attemptId": None,
            "answererType": answerer_type,
            "learnerModelWriteAllowed": False,
            "examResultPath": str(exam_result),
            "sources": [],
            "outputPolicy": {"generatesPdf": False, "writesLearnerModel": False},
        }
    if not attempt_id:
        raise ValueError("user-written mode requires a new --attempt-id")
    for path, role in ((questions_pdf, "questions"), (answers_pdf, "answers"), (submission_pdf, "user-submission")):
        if path is None or not path.is_file():
            raise ValueError(f"user-written mode requires {role} PDF")
    return {
        "schemaVersion": "review-input.v2",
        "reviewMode": "user-written",
        "reviewRunId": review_run_id,
        "examRunId": None,
        "attemptId": attempt_id,
        "answererType": "human",
        "learnerModelWriteAllowed": True,
        "examResultPath": None,
        "sources": [_source(questions_pdf, "questions"), _source(answers_pdf, "answers"), _source(submission_pdf, "user-submission")],
        "outputPolicy": {"generatesPdf": False, "writesLearnerModel": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Route review to exam-result or user-written mode.")
    parser.add_argument("--mode", choices=["exam-result", "user-written"])
    parser.add_argument("--exam-result", type=Path)
    parser.add_argument("--questions-pdf", type=Path)
    parser.add_argument("--answers-pdf", type=Path)
    parser.add_argument("--submission-pdf", type=Path)
    parser.add_argument("--attempt-id")
    parser.add_argument("--review-run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = route_review(args.mode, exam_result=args.exam_result, questions_pdf=args.questions_pdf, answers_pdf=args.answers_pdf, submission_pdf=args.submission_pdf, attempt_id=args.attempt_id, review_run_id=args.review_run_id)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "mode": manifest["reviewMode"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
