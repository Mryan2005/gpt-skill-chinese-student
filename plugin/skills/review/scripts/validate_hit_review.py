"""Validate cross-domain Review Exam Hit enrichment output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STATUSES = {"HIT", "PARTIAL", "MISS", "UNRESOLVED"}
GAP_TYPES = {"mapping_missing", "content_incomplete", "knowledge_missing", "relation_missing", "source_insufficient", "answer_conflict", "question_unreadable", "question_boundary_missing", "question_text_incomplete", "source_evidence_missing", "solution_evidence_insufficient", "answer_provenance_conflict", "card_content_incomplete"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_hit_review(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["hit review report must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") != "review.hit-review.report.v1":
        errors.append("schemaVersion must be review.hit-review.report.v1")
    for field in ("reviewRunId", "subjectId"):
        if not _text(report.get(field)):
            errors.append(f"{field} must be non-empty")
    if not isinstance(report.get("graphSnapshotBefore"), dict):
        errors.append("graphSnapshotBefore is required")
    if report.get("graphSnapshotRecovered") is not None and not isinstance(report.get("graphSnapshotRecovered"), dict):
        errors.append("graphSnapshotRecovered must be an object or null")
    if report.get("graphSnapshotAfter") is not None and not isinstance(report.get("graphSnapshotAfter"), dict):
        errors.append("graphSnapshotAfter must be an object or null")
    for field in ("learnerModelMutation", "examResultMutation", "artifactMutation", "sourceMutation"):
        if report.get(field) is not False:
            errors.append(f"{field} must be false")
    hit_before = report.get("hitBefore")
    if not isinstance(hit_before, dict) or not isinstance(hit_before.get("questionResults"), list) or not isinstance(hit_before.get("coverageSummary"), dict):
        errors.append("hitBefore must contain questionResults and coverageSummary")
    if report.get("hitRecovered") is not None and (not isinstance(report.get("hitRecovered"), dict) or not isinstance(report["hitRecovered"].get("questionResults"), list)):
        errors.append("hitRecovered must contain questionResults when present")
    highlights = report.get("highlights")
    if not isinstance(highlights, list):
        errors.append("highlights must be a list")
        highlights = []
    seen_highlights: set[str] = set()
    for index, item in enumerate(highlights):
        path = f"highlights[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("highlightId", "subjectId", "reviewRunId", "targetType", "targetId", "hitStatus", "highlightType", "coverageStage", "reason", "snapshotId"):
            if not _text(item.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if item.get("highlightId") in seen_highlights:
            errors.append(f"{path}.highlightId is duplicated")
        seen_highlights.add(item.get("highlightId"))
        if item.get("hitStatus") not in {"HIT", "PARTIAL"}:
            errors.append(f"{path}.hitStatus must be HIT or PARTIAL")
        if item.get("coverageStage") not in {"original_exam_hit", "recovered_exam_hit", "enriched_exam_coverage"}:
            errors.append(f"{path}.coverageStage is invalid")
        if item.get("highlightType") not in {"exam_hit_content", "exam_partial_content"}:
            errors.append(f"{path}.highlightType is invalid")
        if not isinstance(item.get("questionIds"), list) or not item["questionIds"]:
            errors.append(f"{path}.questionIds must be non-empty")
        anchor = item.get("contentAnchor")
        if not isinstance(anchor, dict) or not _text(anchor.get("field")) or not _text(anchor.get("excerpt")) or not _text(anchor.get("contentSha256")):
            errors.append(f"{path}.contentAnchor must point to card content")
        if not isinstance(item.get("evidenceRefs"), list) or not item["evidenceRefs"]:
            errors.append(f"{path}.evidenceRefs must be non-empty")
    gaps = report.get("gaps")
    if not isinstance(gaps, list):
        errors.append("gaps must be a list")
        gaps = []
    gap_ids: set[str] = set()
    for index, gap in enumerate(gaps):
        path = f"gaps[{index}]"
        if not isinstance(gap, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("gapId", "researchQuery", "repairOwner", "status"):
            if not _text(gap.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if gap.get("gapType") not in GAP_TYPES:
            errors.append(f"{path}.gapType is invalid")
        if gap.get("gapId") in gap_ids:
            errors.append(f"{path}.gapId is duplicated")
        gap_ids.add(gap.get("gapId"))
        for field in ("questionIds", "cardIds", "missingKnowledge", "evidenceRefs"):
            if not isinstance(gap.get(field), list):
                errors.append(f"{path}.{field} must be a list")
    research = report.get("research")
    if not isinstance(research, dict) or research.get("status") not in {"NOT_NEEDED", "PENDING", "PARTIAL", "COMPLETE", "FAILED"}:
        errors.append("research.status is invalid")
    else:
        supplements = research.get("externalSupplements")
        if not isinstance(supplements, list):
            errors.append("research.externalSupplements must be a list")
        else:
            for index, supplement in enumerate(supplements):
                path = f"research.externalSupplements[{index}]"
                if not isinstance(supplement, dict):
                    errors.append(f"{path} must be an object")
                    continue
                for field in ("supplementId", "sourceUrl", "sourceTitle", "publisher", "accessedAt", "provenanceType", "evidenceStatus"):
                    if not _text(supplement.get(field)):
                        errors.append(f"{path}.{field} must be non-empty")
                if not str(supplement.get("sourceUrl", "")).startswith(("https://", "http://")):
                    errors.append(f"{path}.sourceUrl must be http(s)")
                if supplement.get("provenanceType") != "external_supplement":
                    errors.append(f"{path}.provenanceType must be external_supplement")
                if supplement.get("evidenceStatus") not in {"supported", "needs_verification", "rejected"}:
                    errors.append(f"{path}.evidenceStatus is invalid")
                if not isinstance(supplement.get("supportedClaims"), list) or not supplement["supportedClaims"]:
                    errors.append(f"{path}.supportedClaims must be non-empty")
                if not set(supplement.get("relatedGapIds", [])) & gap_ids:
                    errors.append(f"{path} must point to a detected gap")
    comparison = report.get("comparison")
    if not isinstance(comparison, dict) or comparison.get("status") not in {"NOT_RECHECKED", "RECHECKED"}:
        errors.append("comparison is incomplete")
    overlay = report.get("annotationOverlay")
    if not isinstance(overlay, dict) or overlay.get("schemaVersion") != "review.annotation-overlay.v1" or overlay.get("subjectId") != report.get("subjectId"):
        errors.append("annotationOverlay is inconsistent")
    elif len(overlay.get("annotations", [])) != len(highlights):
        errors.append("annotationOverlay must contain the same highlights")
    for field in ("studyGuideMarkdown", "studyGuideHtml"):
        if not isinstance(report.get(field), str) or not report[field].strip():
            errors.append(f"{field} must be non-empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Review Exam Hit enrichment output.")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_hit_review(report)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print("PASS: validated Review Exam Hit enrichment report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
