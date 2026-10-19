"""Build a complete, evidence-backed exam-hit coverage report."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


STATUSES = {"HIT", "PARTIAL", "MISS", "UNRESOLVED"}
READ_STATUSES = {"READABLE", "UNREADABLE"}
PDF_MODES = {"native_pdf_page_image", "native_pdf_text_and_page"}
FORBIDDEN_CONTENT_FIELDS = {"id", "title", "name", "label"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _refs(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_text(item) for item in value)


def _pdf_errors(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors: list[str] = []
    if value.get("source") != "original_pdf":
        errors.append(f"{path}.source must be original_pdf")
    if not _text(value.get("path")) or not str(value["path"]).lower().endswith(".pdf"):
        errors.append(f"{path}.path must point to an original PDF")
    if value.get("readingMode") not in PDF_MODES:
        errors.append(f"{path}.readingMode must use native PDF reading")
    if value.get("ocrUsed") is not False or value.get("delegatedOcr") is not False:
        errors.append(f"{path} cannot use OCR or delegated OCR")
    if value.get("intermediateTextSources") != []:
        errors.append(f"{path}.intermediateTextSources must be empty")
    return errors


def _page_errors(value: Any, path: str, exam_pdf: dict[str, Any]) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must reference an original PDF page"]
    errors = _pdf_errors({
        "source": value.get("source"),
        "path": value.get("path"),
        "readingMode": value.get("readingMode", exam_pdf.get("readingMode")),
        "ocrUsed": value.get("ocrUsed", exam_pdf.get("ocrUsed")),
        "delegatedOcr": value.get("delegatedOcr", exam_pdf.get("delegatedOcr")),
        "intermediateTextSources": value.get("intermediateTextSources", exam_pdf.get("intermediateTextSources", [])),
    }, path)
    if not isinstance(value.get("page"), int) or value["page"] < 1:
        errors.append(f"{path}.page must be a positive integer")
    return errors


def validate_input(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["input must be an object"]
    errors: list[str] = []
    if data.get("schemaVersion") != "exam.hit.input.v1":
        errors.append("schemaVersion must be exam.hit.input.v1")
    for field in ("examHitRunId", "examId", "subjectId"):
        if not _text(data.get(field)):
            errors.append(f"{field} must be non-empty")
    if data.get("selectionPolicy") != "all_questions":
        errors.append("selectionPolicy must be all_questions; the Exam Hit phase cannot sample")
    exam_pdf = data.get("examPdf")
    errors.extend(_pdf_errors(exam_pdf, "examPdf"))
    snapshot = data.get("snapshot")
    if not isinstance(snapshot, dict):
        errors.append("snapshot must be an object")
    else:
        for field in ("snapshotId", "subjectId", "artifactVersion", "contentSha256", "frozenAt"):
            if not _text(snapshot.get(field)):
                errors.append(f"snapshot.{field} must be non-empty")
        if snapshot.get("subjectId") != data.get("subjectId"):
            errors.append("snapshot.subjectId must match subjectId")
        if snapshot.get("frozen") is not True or snapshot.get("readOnly") is not True:
            errors.append("snapshot must be frozen and read-only")
    cards = data.get("cards")
    card_ids: set[str] = set()
    card_contents: dict[str, dict[str, Any]] = {}
    if not isinstance(cards, list) or not cards:
        errors.append("cards must be a non-empty list")
        cards = []
    for index, card in enumerate(cards):
        path = f"cards[{index}]"
        if not isinstance(card, dict) or not _text(card.get("cardId")):
            errors.append(f"{path}.cardId must be non-empty")
            continue
        if card["cardId"] in card_ids:
            errors.append(f"{path}.cardId is duplicated")
        card_ids.add(card["cardId"])
        content = card.get("content")
        if not isinstance(content, dict) or not any(_text(value) for key, value in content.items() if key not in FORBIDDEN_CONTENT_FIELDS):
            errors.append(f"{path}.content must contain actual non-title card content")
        else:
            card_contents[card["cardId"]] = content
        if not _text(card.get("contentSha256")):
            errors.append(f"{path}.contentSha256 must be non-empty")
    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append("questions must be a non-empty list")
        questions = []
    question_ids: set[str] = set()
    for index, question in enumerate(questions):
        path = f"questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{path} must be an object")
            continue
        qid = question.get("questionId")
        if not _text(qid):
            errors.append(f"{path}.questionId must be non-empty")
        elif qid in question_ids:
            errors.append(f"{path}.questionId is duplicated")
        else:
            question_ids.add(qid)
        errors.extend(_page_errors(question.get("examPage"), f"{path}.examPage", exam_pdf if isinstance(exam_pdf, dict) else {}))
        if question.get("readStatus") not in READ_STATUSES:
            errors.append(f"{path}.readStatus must be READABLE or UNREADABLE")
        required = question.get("requiredKnowledge")
        if question.get("readStatus") == "READABLE" and (not isinstance(required, list) or not required):
            errors.append(f"{path}.requiredKnowledge must be non-empty for a readable question")
        if not isinstance(required, list):
            errors.append(f"{path}.requiredKnowledge must be a list")
        result = question.get("hitResult")
        if not isinstance(result, dict):
            errors.append(f"{path}.hitResult must be an object")
            continue
        if result.get("hitStatus") not in STATUSES:
            errors.append(f"{path}.hitResult.hitStatus is invalid")
        if not isinstance(result.get("supportingCardIds"), list):
            errors.append(f"{path}.hitResult.supportingCardIds must be a list")
        refs = result.get("supportingCardContentRefs")
        if not isinstance(refs, list):
            errors.append(f"{path}.hitResult.supportingCardContentRefs must be a list")
            refs = []
        ref_ids: set[str] = set()
        for ref_index, ref in enumerate(refs):
            ref_path = f"{path}.hitResult.supportingCardContentRefs[{ref_index}]"
            if not isinstance(ref, dict) or not _text(ref.get("cardId")) or not _text(ref.get("field")) or not _text(ref.get("excerpt")) or not _text(ref.get("contentSha256")):
                errors.append(f"{ref_path} must point to actual card content")
                continue
            if ref.get("field") in FORBIDDEN_CONTENT_FIELDS:
                errors.append(f"{ref_path}.field cannot be title-only evidence")
            if ref["cardId"] not in card_contents:
                errors.append(f"{ref_path}.cardId is not in the frozen card catalog")
            else:
                content_value = card_contents[ref["cardId"]].get(ref["field"])
                if not _text(content_value) or ref["excerpt"] not in str(content_value):
                    errors.append(f"{ref_path}.excerpt is not present in the referenced card content")
            ref_ids.add(ref["cardId"])
        if set(result.get("supportingCardIds", [])) != ref_ids:
            errors.append(f"{path}.hitResult.supportingCardIds must match content references")
        for field in ("supportedReasoning", "evidenceRefs"):
            if field == "evidenceRefs":
                if not _refs(result.get(field)):
                    errors.append(f"{path}.hitResult.evidenceRefs must be non-empty")
            elif result.get("hitStatus") != "UNRESOLVED" and not _text(result.get(field)):
                errors.append(f"{path}.hitResult.{field} must be non-empty")
        if result.get("hitStatus") == "UNRESOLVED" and not _text(result.get("unresolvedReason")):
            errors.append(f"{path}.hitResult.unresolvedReason is required for UNRESOLVED")
        if result.get("hitStatus") in {"PARTIAL", "MISS"} and not isinstance(result.get("missingKnowledge"), list) or result.get("hitStatus") in {"PARTIAL", "MISS"} and not result.get("missingKnowledge"):
            errors.append(f"{path}.hitResult.missingKnowledge is required for PARTIAL or MISS")
        if result.get("hitStatus") == "HIT" and result.get("missingKnowledge") not in ([], None):
            errors.append(f"{path}.HIT cannot declare missingKnowledge")
        confidence = result.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            errors.append(f"{path}.hitResult.confidence must be between 0 and 1")
    return errors


def _summary(question_results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {status: 0 for status in STATUSES}
    card_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"HIT": 0, "PARTIAL": 0, "questionIds": []})
    for question in question_results:
        result = question["hitResult"]
        status = result["hitStatus"]
        counts[status] += 1
        if status in {"HIT", "PARTIAL"}:
            for card_id in result.get("supportingCardIds", []):
                card_stats[card_id][status] += 1
                card_stats[card_id]["questionIds"].append(question["questionId"])
    total = len(question_results)
    determinate = total - counts["UNRESOLVED"]
    return {
        "totalQuestions": total,
        "counts": counts,
        "determinateQuestions": determinate,
        "completeCoverageRate": counts["HIT"] / total if total else 0,
        "determinateCoverageRate": counts["HIT"] / determinate if determinate else None,
        "cardHitStatistics": [{"cardId": card_id, **values} for card_id, values in sorted(card_stats.items())],
        "derivedFocusFromObservedHits": [card_id for card_id, values in sorted(card_stats.items(), key=lambda item: (-item[1]["HIT"], -item[1]["PARTIAL"], item[0])) if values["HIT"] > 0],
    }


def build_report(data: dict[str, Any]) -> dict[str, Any]:
    errors = validate_input(data)
    if errors:
        raise ValueError("; ".join(errors))
    questions = data["questions"]
    question_results = [{
        "questionId": question["questionId"],
        "examId": data["examId"],
        "examPage": question["examPage"],
        "readStatus": question["readStatus"],
        "requiredKnowledge": question.get("requiredKnowledge", []),
        "hitResult": question["hitResult"],
    } for question in questions]
    summary = _summary(question_results)
    report = {
        "schemaVersion": "exam.hit.report.v1",
        "examHitRunId": data["examHitRunId"],
        "examId": data["examId"],
        "subjectId": data["subjectId"],
        "auditStatus": "COMPLETE" if summary["counts"]["UNRESOLVED"] == 0 else "PARTIAL",
        "selectionPolicy": "all_questions",
        "generatedFromAllQuestions": True,
        "preselectedFocusUsed": False,
        "examPdf": data["examPdf"],
        "snapshot": data["snapshot"],
        "questionResults": question_results,
        "coverageSummary": summary,
        "sourceMutation": False,
        "examResultMutation": False,
        "learnerModelMutation": False,
        "snapshotMutated": False,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a question-by-question exam-hit report.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        report = build_report(data)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "auditStatus": report["auditStatus"], "counts": report["coverageSummary"]["counts"]}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
