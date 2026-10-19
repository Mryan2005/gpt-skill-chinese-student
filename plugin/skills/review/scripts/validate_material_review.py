"""Validate material-review output at the material/learner boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_hit_review import validate_hit_review


MATERIAL_SCHEMA_VERSIONS = {"material-review.report.v1", "material-review.report.v2"}
MATERIAL_HIGHLIGHTS = {"confirmed_weakness", "suspected_weakness"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_overlay(overlay: Any, errors: list[str]) -> None:
    if not isinstance(overlay, dict):
        errors.append("annotationOverlay must be an object")
        return
    if overlay.get("schemaVersion") != "review.annotation-overlay.v1":
        errors.append("annotationOverlay.schemaVersion is invalid")
    annotations = overlay.get("annotations")
    if not isinstance(annotations, list):
        errors.append("annotationOverlay.annotations must be a list")
        return
    seen: set[str] = set()
    for index, annotation in enumerate(annotations):
        path = f"annotationOverlay.annotations[{index}]"
        if not isinstance(annotation, dict):
            errors.append(f"{path} must be an object")
            continue
        highlight_id = annotation.get("highlightId")
        if not _text(highlight_id):
            errors.append(f"{path}.highlightId must be non-empty")
        elif highlight_id in seen:
            errors.append(f"{path}.highlightId is duplicated")
        seen.add(highlight_id)
        for field in ("targetType", "targetId", "highlightType", "reason", "renderHint"):
            if not _text(annotation.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if not isinstance(annotation.get("evidenceRefs"), list) or not annotation["evidenceRefs"]:
            errors.append(f"{path}.evidenceRefs must be non-empty")
        if annotation.get("highlightType") in MATERIAL_HIGHLIGHTS:
            errors.append(f"{path} cannot contain learner-weakness highlight {annotation['highlightType']}")
        if annotation.get("status") == "unresolved_anchor" and (annotation.get("anchor") or {}).get("status") == "resolved":
            errors.append(f"{path}.unresolved_anchor cannot have a resolved anchor")


def validate_material_review(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["material review must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") not in MATERIAL_SCHEMA_VERSIONS:
        errors.append("schemaVersion must be a material-review report version")
    if report.get("schemaVersion") == "material-review.report.v2":
        if report.get("reviewMode") != "material":
            errors.append("reviewMode must be material")
        if report.get("learnerModelMutation") is not False:
            errors.append("learnerModelMutation must be false")
        if report.get("artifactMutation") is not False:
            errors.append("artifactMutation must be false")
        if report.get("sourceMutation") is not False:
            errors.append("sourceMutation must be false")
        for field in ("coverage", "blockerAnalysis", "unansweredAnalysis", "focuses", "questionAnalyses", "questionIndex", "learningOrder", "questionLearningOrder", "learningTasks", "retestPlans", "learnerModel", "annotationOverlay", "examResultIntegrity", "studyGuideHtml"):
            if field not in report:
                errors.append(f"{field} is required for material-review.report.v2")
    for field in ("reviewRunId", "examRunId", "subjectId"):
        if not _text(report.get(field)):
            errors.append(f"{field} must be non-empty")
    if report.get("answererType") not in {"human", "agent", "model", "unknown"}:
        errors.append("answererType is invalid")
    if report.get("learnerModelWriteAllowed") is not False:
        errors.append("Material Review cannot write the Learner Model")
    if report.get("examResultMutation") is not False:
        errors.append("examResultMutation must be false")
    if not isinstance(report.get("studyGuideMarkdown"), str) or not report["studyGuideMarkdown"].strip():
        errors.append("studyGuideMarkdown must be non-empty")
    if not isinstance(report.get("studyGuideHtml"), str) or not report["studyGuideHtml"].strip():
        errors.append("studyGuideHtml must be non-empty")
    for field in ("counts", "blockers", "annotations", "routes"):
        if field in report and not isinstance(report[field], (dict, list)):
            errors.append(f"{field} has an invalid type")
    focuses = report.get("focuses", [])
    if not isinstance(focuses, list):
        errors.append("focuses must be a list")
    else:
        seen_cards: set[str] = set()
        for index, focus in enumerate(focuses):
            path = f"focuses[{index}]"
            if not isinstance(focus, dict):
                errors.append(f"{path} must be an object")
                continue
            card_id = focus.get("cardId")
            if not _text(card_id) or card_id == "__unmapped__":
                errors.append(f"{path}.cardId must be a real canonical card ID")
            elif card_id in seen_cards:
                errors.append(f"{path}.cardId is duplicated")
            seen_cards.add(card_id)
            if not isinstance(focus.get("questionIds"), list):
                errors.append(f"{path}.questionIds must be a list")
            if not isinstance(focus.get("evidenceRefs"), list) or not focus["evidenceRefs"]:
                errors.append(f"{path}.evidenceRefs must be non-empty")
    if not isinstance(report.get("learningOrder", []), list):
        errors.append("learningOrder must be a list")
    analyses = report.get("questionAnalyses", [])
    if not isinstance(analyses, list):
        errors.append("questionAnalyses must be a list")
    else:
        seen_questions: set[str] = set()
        for index, analysis in enumerate(analyses):
            path = f"questionAnalyses[{index}]"
            if not isinstance(analysis, dict):
                errors.append(f"{path} must be an object")
                continue
            question_id = analysis.get("questionId")
            if not _text(question_id):
                errors.append(f"{path}.questionId must be non-empty")
            elif question_id in seen_questions:
                errors.append(f"{path}.questionId is duplicated")
            seen_questions.add(question_id)
            if "__unmapped__" in analysis.get("cardIds", []):
                errors.append(f"{path}.cardIds cannot contain __unmapped__")
            if analysis.get("mappingStatus") not in {"mapped", "unmapped"}:
                errors.append(f"{path}.mappingStatus is invalid")
            if not isinstance(analysis.get("coreKnowledge"), dict) or not analysis["coreKnowledge"].get("items"):
                errors.append(f"{path}.coreKnowledge must contain evidence-backed items")
            if not isinstance(analysis.get("sourceRefs"), list) or not analysis["sourceRefs"]:
                errors.append(f"{path}.sourceRefs must be non-empty")
    if not isinstance(report.get("questionLearningOrder", []), list):
        errors.append("questionLearningOrder must be a list")
    _validate_overlay(report.get("annotationOverlay"), errors)
    if "examHitReview" in report:
        errors.extend(f"examHitReview: {error}" for error in validate_hit_review(report["examHitReview"]))
    learner_model = report.get("learnerModel")
    if isinstance(learner_model, dict):
        for field in ("observationsAppended", "masteryChanges", "selfReportChanges"):
            if learner_model.get(field, 0) != 0:
                errors.append(f"learnerModel.{field} must be 0 for Material Review")
    integrity = report.get("examResultIntegrity")
    if isinstance(integrity, dict):
        if integrity.get("mutation") is not False or integrity.get("unchanged") is not True:
            errors.append("examResultIntegrity must prove an unchanged Exam Result")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a material review report.")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_material_review(report)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print("PASS: validated material review report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
