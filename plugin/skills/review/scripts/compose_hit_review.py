"""Compose cross-domain Exam Hit highlights, gap routes, and research handoffs."""

from __future__ import annotations

import argparse
import copy
import html
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "review.hit-review.report.v1"
STATUSES = {"HIT", "PARTIAL", "MISS", "UNRESOLVED"}
STATUS_RANK = {"MISS": 0, "UNRESOLVED": 0, "PARTIAL": 1, "HIT": 2}
GAP_TYPES = {"mapping_missing", "content_incomplete", "knowledge_missing", "relation_missing", "source_insufficient", "answer_conflict", "question_unreadable", "question_boundary_missing", "question_text_incomplete", "source_evidence_missing", "solution_evidence_insufficient", "answer_provenance_conflict", "card_content_incomplete"}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _question_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("questionId")): item for item in _list(report.get("questionResults")) if isinstance(item, dict) and _text(item.get("questionId"))}


def _cards(catalog: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(catalog, dict):
        return {}
    return {str(item.get("cardId") or item.get("id")): item for item in _list(catalog.get("cards", catalog.get("nodes"))) if isinstance(item, dict) and _text(item.get("cardId") or item.get("id"))}


def _coverage_summary(hit: dict[str, Any]) -> dict[str, Any]:
    summary = hit.get("coverageSummary")
    return summary if isinstance(summary, dict) else {"totalQuestions": len(_list(hit.get("questionResults"))), "counts": {status: 0 for status in STATUSES}, "completeCoverageRate": 0, "determinateCoverageRate": None}


def _normalize_hit_report(value: dict[str, Any]) -> dict[str, Any]:
    """Allow Review to consume frozen Exam Result Hit records directly."""

    if value.get("schemaVersion") == "exam.hit.report.v1":
        return value
    if value.get("schemaVersion") != "exam-record.v1":
        raise ValueError("hit input must be exam.hit.report.v1 or a frozen exam-record.v1")
    if value.get("state") != "CLOSED":
        raise ValueError("Review can consume Exam Hit only from a CLOSED Exam Result")
    isolation = value.get("executionIsolation")
    if not isinstance(isolation, dict) or isolation.get("verified") is not True:
        raise ValueError("Exam Result Hit isolation must be verified before Review consumption")
    snapshot = value.get("snapshot") if isinstance(value.get("snapshot"), dict) else {}
    snapshot = {
        "snapshotId": snapshot.get("id"),
        "subjectId": snapshot.get("subjectId") or (value.get("subject") or {}).get("id"),
        "artifactVersion": snapshot.get("artifactVersion"),
        "contentSha256": snapshot.get("contentSha256") or snapshot.get("artifactHash") or snapshot.get("artifactVersion"),
        "frozenAt": snapshot.get("frozenAt"),
        "frozen": snapshot.get("frozen") is True,
        "readOnly": True,
    }
    results: list[dict[str, Any]] = []
    counts = {status: 0 for status in STATUSES}
    for question in _list(value.get("questions")):
        if not isinstance(question, dict):
            continue
        hit = question.get("hit")
        if not isinstance(hit, dict):
            raise ValueError(f"Exam Result question {question.get('questionId')} has no frozen Hit record")
        status = hit.get("hitStatus")
        if status not in STATUSES:
            raise ValueError(f"Exam Result question {question.get('questionId')} has an invalid Hit status")
        counts[status] += 1
        first_pass = question.get("firstPass") if isinstance(question.get("firstPass"), dict) else {}
        results.append({
            "questionId": question.get("questionId"),
            "examId": value.get("examId"),
            "examPage": question.get("examPage"),
            "readStatus": "UNREADABLE" if first_pass.get("attemptStatus") == "BLOCKED_BY_UNREADABLE_QUESTION" else "READABLE",
            "requiredKnowledge": hit.get("requiredKnowledge", []),
            "hitResult": {
                "hitStatus": status,
                "supportingCardIds": hit.get("supportingCardIds", []),
                "supportingCardContentRefs": hit.get("supportingContentRefs", []),
                "supportedReasoning": hit.get("supportedReasoning") or hit.get("hitReasoning") or f"Frozen Exam Hit recorded {status} using the cited card-content evidence.",
                "missingKnowledge": hit.get("missingKnowledge", []),
                "mappingIssues": hit.get("mappingIssues", []),
                "evidenceRefs": hit.get("hitEvidenceRefs", []),
                "unresolvedReason": hit.get("unresolvedReason"),
                "confidence": hit.get("confidence", 1 if status != "UNRESOLVED" else 0),
            },
        })
    total = len(results)
    determinate = total - counts["UNRESOLVED"]
    return {
        "schemaVersion": "exam.hit.report.v1",
        "examHitRunId": value.get("examId"),
        "examId": value.get("examId"),
        "subjectId": snapshot.get("subjectId"),
        "auditStatus": "COMPLETE" if counts["UNRESOLVED"] == 0 else "PARTIAL",
        "selectionPolicy": "all_questions",
        "generatedFromAllQuestions": True,
        "preselectedFocusUsed": False,
        "snapshot": snapshot,
        "questionResults": results,
        "coverageSummary": {"totalQuestions": total, "counts": counts, "determinateQuestions": determinate, "completeCoverageRate": counts["HIT"] / total if total else 0, "determinateCoverageRate": counts["HIT"] / determinate if determinate else None},
        "sourceMutation": False,
        "examResultMutation": False,
        "learnerModelMutation": False,
        "snapshotMutated": False,
    }


def _snapshot_id(hit: dict[str, Any]) -> str:
    return _text((hit.get("snapshot") or {}).get("snapshotId")) or "unknown-snapshot"


def _classify_gap(question: dict[str, Any]) -> str:
    result = question.get("hitResult", {}) if isinstance(question.get("hitResult"), dict) else {}
    status = result.get("hitStatus")
    explicit = _text(result.get("failureReason"))
    if explicit in GAP_TYPES:
        return explicit
    issues = {str(item).casefold() for item in _list(result.get("mappingIssues"))}
    missing = " ".join(str(item).casefold() for item in _list(result.get("missingKnowledge")))
    if "answer" in " ".join(issues) or "conflict" in " ".join(issues):
        return "answer_conflict"
    if question.get("readStatus") == "UNREADABLE" or status == "UNRESOLVED":
        return "question_unreadable"
    if any(token in " ".join(issues) for token in ("mapping", "no_question_mapping", "direct_mapping")):
        return "mapping_missing"
    if any(token in " ".join(issues) for token in ("relation", "bridge")):
        return "relation_missing"
    if status == "PARTIAL" and result.get("supportingCardIds"):
        return "content_incomplete"
    if status == "MISS" or missing:
        return "knowledge_missing"
    return "source_insufficient"


def _gap_owner(gap_type: str) -> str:
    return {"mapping_missing": "learn", "content_incomplete": "learn", "knowledge_missing": "learn", "relation_missing": "learn", "card_content_incomplete": "learn", "source_insufficient": "check", "source_evidence_missing": "check", "question_boundary_missing": "check", "question_text_incomplete": "check", "question_unreadable": "check", "solution_evidence_insufficient": "check", "answer_conflict": "amend", "answer_provenance_conflict": "amend"}.get(gap_type, "learn")


def _gap_records(hit_before: dict[str, Any]) -> list[dict[str, Any]]:
    gaps: dict[tuple[str, str], dict[str, Any]] = {}
    for question in _list(hit_before.get("questionResults")):
        if not isinstance(question, dict):
            continue
        result = question.get("hitResult", {})
        if not isinstance(result, dict) or result.get("hitStatus") not in {"PARTIAL", "MISS", "UNRESOLVED"}:
            continue
        gap_type = _classify_gap(question)
        missing = _list(result.get("missingKnowledge")) or [_text(result.get("unresolvedReason")) or "Coverage could not be verified from the supplied evidence."]
        normalized = " | ".join(sorted({_text(item).casefold() for item in missing if _text(item)}))
        key = (gap_type, normalized or str(question.get("questionId")))
        item = gaps.setdefault(key, {
            "gapId": f"gap-{len(gaps) + 1:03d}",
            "gapType": gap_type,
            "questionIds": [],
            "cardIds": [],
            "missingKnowledge": [],
            "evidenceRefs": [],
            "repairOwner": _gap_owner(gap_type),
            "failureReasons": [],
            "status": "open",
        })
        item["questionIds"].append(question.get("questionId"))
        item["cardIds"].extend(result.get("supportingCardIds", []))
        item["missingKnowledge"].extend(missing)
        item["evidenceRefs"].extend(result.get("evidenceRefs", []))
        item["failureReasons"].append(gap_type)
    for item in gaps.values():
        item["questionIds"] = sorted(set(item["questionIds"]))
        item["cardIds"] = sorted(set(item["cardIds"]))
        item["missingKnowledge"] = sorted(set(_text(value) for value in item["missingKnowledge"] if _text(value)))
        item["evidenceRefs"] = sorted(set(_text(value) for value in item["evidenceRefs"] if _text(value)))
        item["failureReasons"] = sorted(set(item["failureReasons"]))
        item["researchQuery"] = " ".join(item["missingKnowledge"]) or f"{item['gapType']} knowledge for questions {' '.join(item['questionIds'])}"
    return list(gaps.values())


def _validate_supplement(supplement: Any, gap_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(supplement, dict):
        return ["external supplement must be an object"]
    for field in ("supplementId", "sourceUrl", "sourceTitle", "publisher", "accessedAt", "provenanceType", "evidenceStatus"):
        if not _text(supplement.get(field)):
            errors.append(f"externalSupplements.{field} must be non-empty")
    if not str(supplement.get("sourceUrl", "")).startswith(("https://", "http://")):
        errors.append("externalSupplements.sourceUrl must be http(s)")
    if supplement.get("provenanceType") != "external_supplement":
        errors.append("externalSupplements.provenanceType must be external_supplement")
    if supplement.get("evidenceStatus") not in {"supported", "needs_verification", "rejected"}:
        errors.append("externalSupplements.evidenceStatus is invalid")
    if not isinstance(supplement.get("supportedClaims"), list) or not supplement["supportedClaims"]:
        errors.append("externalSupplements.supportedClaims must be non-empty")
    related = set(supplement.get("relatedGapIds", []))
    if not related & gap_ids:
        errors.append("externalSupplements must relate to a detected gap")
    return errors


def _highlights(hit: dict[str, Any], catalog: dict[str, Any] | None, *, stage: str, review_run_id: str) -> list[dict[str, Any]]:
    card_map = _cards(catalog)
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    snapshot_id = _snapshot_id(hit)
    for question in _list(hit.get("questionResults")):
        if not isinstance(question, dict):
            continue
        result = question.get("hitResult", {})
        if not isinstance(result, dict) or result.get("hitStatus") not in {"HIT", "PARTIAL"}:
            continue
        for ref in _list(result.get("supportingCardContentRefs")):
            if not isinstance(ref, dict) or not _text(ref.get("cardId")) or not _text(ref.get("field")) or not _text(ref.get("excerpt")):
                continue
            key = (ref["cardId"], ref["field"], ref["excerpt"], stage)
            annotation = grouped.setdefault(key, {
                "highlightId": f"exam-hit-{review_run_id}-{stage}-{len(grouped) + 1:03d}",
                "subjectId": hit.get("subjectId", "unknown"),
                "reviewRunId": review_run_id,
                "targetType": "card",
                "targetId": ref["cardId"],
                "questionIds": [],
                "cardVersion": (card_map.get(ref["cardId"], {}).get("derivedVersion") or card_map.get(ref["cardId"], {}).get("version") or (hit.get("snapshot") or {}).get("artifactVersion")),
                "contentAnchor": {"status": "resolved" if ref["cardId"] in card_map or not card_map else "unresolved", "field": ref["field"], "excerpt": ref["excerpt"], "contentSha256": ref.get("contentSha256")},
                "hitStatus": result["hitStatus"],
                "highlightType": "exam_hit_content" if result["hitStatus"] == "HIT" else "exam_partial_content",
                "coverageStage": stage,
                "evidenceRefs": [],
                "reason": result.get("supportedReasoning", "The question's required operation is supported by this card content."),
                "snapshotId": snapshot_id,
                "priority": "high" if result["hitStatus"] == "HIT" else "medium",
                "evidenceStrength": "confirmed" if result["hitStatus"] == "HIT" else "supported",
                "labels": ["exam-hit", stage],
                "actionHint": "Open the cited card content and linked question." if result["hitStatus"] == "HIT" else "Read the missing knowledge gap before treating this card as sufficient.",
                "renderHint": "highlight-content-anchor",
                "status": "active",
                "anchor": {"status": "resolved" if ref["cardId"] in card_map or not card_map else "unresolved", "locator": f"card:{ref['cardId']}#{ref['field']}"},
            })
            annotation["questionIds"].append(question.get("questionId"))
            annotation["evidenceRefs"].extend(result.get("evidenceRefs", []))
    for annotation in grouped.values():
        annotation["questionIds"] = sorted(set(annotation["questionIds"]))
        annotation["evidenceRefs"] = sorted(set(annotation["evidenceRefs"]))
    return list(grouped.values())


def _compare(before: dict[str, Any], after: dict[str, Any] | None) -> dict[str, Any]:
    before_summary = _coverage_summary(before)
    if not after:
        return {"status": "NOT_RECHECKED", "before": before_summary, "after": None, "improvedQuestionIds": [], "worsenedQuestionIds": [], "unchangedQuestionIds": []}
    before_map = _question_map(before)
    after_map = _question_map(after)
    improved: list[str] = []
    worsened: list[str] = []
    unchanged: list[str] = []
    for question_id, after_question in after_map.items():
        before_status = (before_map.get(question_id, {}).get("hitResult") or {}).get("hitStatus", "UNRESOLVED")
        after_status = (after_question.get("hitResult") or {}).get("hitStatus", "UNRESOLVED")
        if STATUS_RANK.get(after_status, 0) > STATUS_RANK.get(before_status, 0):
            improved.append(question_id)
        elif STATUS_RANK.get(after_status, 0) < STATUS_RANK.get(before_status, 0):
            worsened.append(question_id)
        else:
            unchanged.append(question_id)
    return {"status": "RECHECKED", "before": before_summary, "after": _coverage_summary(after), "improvedQuestionIds": sorted(improved), "worsenedQuestionIds": sorted(worsened), "unchangedQuestionIds": sorted(unchanged)}


def _research(gaps: list[dict[str, Any]], supplements: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    gap_ids = {item["gapId"] for item in gaps}
    for supplement in supplements:
        errors.extend(_validate_supplement(supplement, gap_ids))
    supported_gap_ids = {gap_id for supplement in supplements if supplement.get("evidenceStatus") == "supported" for gap_id in supplement.get("relatedGapIds", [])}
    if not gaps:
        status = "NOT_NEEDED"
    elif errors:
        status = "FAILED"
    elif supported_gap_ids >= gap_ids:
        status = "COMPLETE"
    elif supplements:
        status = "PARTIAL"
    else:
        status = "PENDING"
    return {"status": status, "queries": [{"gapId": gap["gapId"], "query": gap["researchQuery"], "status": "resolved" if gap["gapId"] in supported_gap_ids else "pending"} for gap in gaps], "externalSupplements": supplements, "unresolvedGapIds": sorted(gap_ids - supported_gap_ids), "errors": errors}, errors


def _learn_handoffs(gaps: list[dict[str, Any]], research: dict[str, Any]) -> list[dict[str, Any]]:
    supported = {gap_id for supplement in research.get("externalSupplements", []) if supplement.get("evidenceStatus") == "supported" for gap_id in supplement.get("relatedGapIds", [])}
    return [{"handoffId": f"learn-{gap['gapId']}", "gapId": gap["gapId"], "owner": "learn", "action": "update_existing_card" if gap["cardIds"] else "create_domain_record", "questionIds": gap["questionIds"], "cardIds": gap["cardIds"], "evidenceRefs": gap["evidenceRefs"], "externalSupplementIds": [item.get("supplementId") for item in research.get("externalSupplements", []) if gap["gapId"] in item.get("relatedGapIds", [])], "status": "ready" if gap["gapId"] in supported else "blocked_until_reliable_evidence"} for gap in gaps if gap["gapType"] in {"content_incomplete", "knowledge_missing", "relation_missing", "mapping_missing"}]


def _markdown(report: dict[str, Any]) -> str:
    before = report["comparison"]["before"]
    lines = [f"# Exam Hit Review: {report['subjectId']}", "", "This report is a derived overlay. It does not modify Source, the frozen Exam Result, or Learner State.", "", "## Coverage before enrichment", "", f"- Total questions: **{before.get('totalQuestions', 0)}**", f"- HIT: **{before.get('counts', {}).get('HIT', 0)}**", f"- PARTIAL: **{before.get('counts', {}).get('PARTIAL', 0)}**", f"- MISS: **{before.get('counts', {}).get('MISS', 0)}**", f"- UNRESOLVED: **{before.get('counts', {}).get('UNRESOLVED', 0)}**", f"- Complete coverage rate: **{before.get('completeCoverageRate', 0):.1%}**", "", "## Content highlights", ""]
    for annotation in report["highlights"]:
        lines.extend([f"### {annotation['targetId']} · {annotation['contentAnchor']['field']}", f"- Questions: {', '.join(annotation['questionIds'])}", f"- Stage: `{annotation['coverageStage']}`; status: `{annotation['hitStatus']}`", f"- Content: `{annotation['contentAnchor']['excerpt']}`", f"- Reason: {annotation['reason']}", f"- Evidence: {', '.join(annotation['evidenceRefs'])}", ""])
    lines.extend(["## Knowledge gaps", ""])
    for gap in report["gaps"]:
        lines.extend([f"### {gap['gapId']} · `{gap['gapType']}`", f"- Questions: {', '.join(gap['questionIds'])}", f"- Missing: {', '.join(gap['missingKnowledge'])}", f"- Research: `{gap['researchQuery']}`", f"- Repair owner: `{gap['repairOwner']}`", ""])
    lines.extend(["## Research and enrichment", "", f"- Research status: `{report['research']['status']}`", f"- External supplements: **{len(report['research']['externalSupplements'])}**", f"- Learn handoffs: **{len(report['learnHandoffs'])}**"])
    for supplement in report["research"]["externalSupplements"]:
        lines.append(f"- Supplement `{supplement.get('supplementId')}`: [{supplement.get('sourceTitle')}]({supplement.get('sourceUrl')}) — {supplement.get('evidenceStatus')}; claims: {'; '.join(str(item) for item in supplement.get('supportedClaims', []))}")
    if report["comparison"]["status"] == "RECHECKED":
        lines.extend(["", "## Before / after", f"- Improved questions: {', '.join(report['comparison']['improvedQuestionIds']) or 'none'}", f"- Worsened questions: {', '.join(report['comparison']['worsenedQuestionIds']) or 'none'}"])
    return "\n".join(lines)


def _html_section(report: dict[str, Any]) -> str:
    esc = lambda value: html.escape(str(value), quote=True)
    blocks = [f"<section id=\"exam-hit-review\" class=\"exam-hit-review\"><h2>Exam Hit Review: {esc(report['subjectId'])}</h2><p class=\"notice\">Content-level highlights and evidence-backed gaps. Source, Exam Result, and Learner State were not modified.</p>"]
    before = report["comparison"]["before"]
    blocks.append(f"<div class=\"coverage\"><strong>Before enrichment:</strong> HIT {before.get('counts', {}).get('HIT', 0)} · PARTIAL {before.get('counts', {}).get('PARTIAL', 0)} · MISS {before.get('counts', {}).get('MISS', 0)} · UNRESOLVED {before.get('counts', {}).get('UNRESOLVED', 0)} · complete coverage {before.get('completeCoverageRate', 0):.1%}</div>")
    blocks.append("<h3>Exam-hit content highlights</h3><div class=\"hit-highlights\">")
    for annotation in report["highlights"]:
        blocks.append(f"<article class=\"hit-card {esc(annotation['hitStatus'].lower())}\" id=\"{esc(annotation['highlightId'])}\"><h4><a href=\"#card-{esc(annotation['targetId'])}\">{esc(annotation['targetId'])}</a> · {esc(annotation['contentAnchor']['field'])}</h4><p><mark>{esc(annotation['contentAnchor']['excerpt'])}</mark></p><p>Questions: {esc(', '.join(annotation['questionIds']))} · stage: <code>{esc(annotation['coverageStage'])}</code></p><p>{esc(annotation['reason'])}</p></article>")
    blocks.append("</div><h3>Knowledge gaps and research</h3><ul>")
    for gap in report["gaps"]:
        blocks.append(f"<li><strong>{esc(gap['gapId'])}</strong> <code>{esc(gap['gapType'])}</code> — questions {esc(', '.join(gap['questionIds']))}; missing: {esc(', '.join(gap['missingKnowledge']))}; research: {esc(gap['researchQuery'])}</li>")
    blocks.append(f"</ul><p>Research status: <code>{esc(report['research']['status'])}</code>; external supplements: {len(report['research']['externalSupplements'])}; learn handoffs: {len(report['learnHandoffs'])}.</p><ul class=\"supplements\">")
    for supplement in report["research"]["externalSupplements"]:
        blocks.append(f"<li><a href=\"{esc(supplement.get('sourceUrl'))}\">{esc(supplement.get('sourceTitle'))}</a> — {esc(supplement.get('publisher'))}; status <code>{esc(supplement.get('evidenceStatus'))}</code>; {esc('; '.join(str(item) for item in supplement.get('supportedClaims', [])))}</li>")
    blocks.append("</ul>")
    if report["comparison"]["status"] == "RECHECKED":
        blocks.append(f"<h3>Before / after</h3><p>Improved: {esc(', '.join(report['comparison']['improvedQuestionIds']) or 'none')}; worsened: {esc(', '.join(report['comparison']['worsenedQuestionIds']) or 'none')}.</p>")
    blocks.append("</section>")
    return "".join(blocks)


def compose_hit_review(hit_before: dict[str, Any], *, review_run_id: str, subject_id: str, catalog: dict[str, Any] | None = None, hit_recovered: dict[str, Any] | None = None, hit_after: dict[str, Any] | None = None, catalog_after: dict[str, Any] | None = None, supplements: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    hit_before = _normalize_hit_report(hit_before)
    if hit_recovered is not None:
        hit_recovered = _normalize_hit_report(hit_recovered)
    if hit_after is not None:
        hit_after = _normalize_hit_report(hit_after)
    if hit_before.get("schemaVersion") != "exam.hit.report.v1":
        raise ValueError("hit_before must be exam.hit.report.v1")
    if hit_after is not None and hit_after.get("schemaVersion") != "exam.hit.report.v1":
        raise ValueError("hit_after must be exam.hit.report.v1")
    supplements = supplements or []
    gaps = _gap_records(hit_recovered or hit_before)
    research, research_errors = _research(gaps, supplements)
    highlights = _highlights(hit_before, catalog, stage="original_exam_hit", review_run_id=review_run_id)
    if hit_recovered:
        highlights.extend(_highlights(hit_recovered, catalog, stage="recovered_exam_hit", review_run_id=review_run_id))
    if hit_after:
        highlights.extend(_highlights(hit_after, catalog_after or catalog, stage="enriched_exam_coverage", review_run_id=review_run_id))
    # Keep one record per stable content anchor and stage; a second run must not duplicate counts.
    unique: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for item in highlights:
        key = (item["targetId"], item["contentAnchor"]["field"], item["contentAnchor"]["excerpt"], item["coverageStage"])
        if key in unique:
            unique[key]["questionIds"] = sorted(set(unique[key]["questionIds"]) | set(item["questionIds"]))
            unique[key]["evidenceRefs"] = sorted(set(unique[key]["evidenceRefs"]) | set(item["evidenceRefs"]))
        else:
            unique[key] = item
    highlights = list(unique.values())
    report = {
        "schemaVersion": SCHEMA_VERSION,
        "reviewRunId": review_run_id,
        "subjectId": subject_id,
        "graphSnapshotBefore": hit_before.get("snapshot"),
        "graphSnapshotRecovered": hit_recovered.get("snapshot") if hit_recovered else None,
        "graphSnapshotAfter": hit_after.get("snapshot") if hit_after else None,
        "hitBefore": {"runId": hit_before.get("examHitRunId"), "snapshot": hit_before.get("snapshot"), "coverageSummary": _coverage_summary(hit_before), "questionResults": hit_before.get("questionResults", [])},
        "hitRecovered": {"runId": hit_recovered.get("examHitRunId"), "snapshot": hit_recovered.get("snapshot"), "coverageSummary": _coverage_summary(hit_recovered), "questionResults": hit_recovered.get("questionResults", [])} if hit_recovered else None,
        "hitAfter": {"runId": hit_after.get("examHitRunId"), "snapshot": hit_after.get("snapshot"), "coverageSummary": _coverage_summary(hit_after), "questionResults": hit_after.get("questionResults", [])} if hit_after else None,
        "highlights": highlights,
        "gaps": gaps,
        "research": research,
        "learnHandoffs": _learn_handoffs(gaps, research),
        "comparison": {"status": "RECHECKED" if hit_after or hit_recovered else "NOT_RECHECKED", "before": _coverage_summary(hit_before), "after": _coverage_summary(hit_after) if hit_after else None, "recovery": _compare(hit_before, hit_recovered) if hit_recovered else None, "enrichment": _compare(hit_recovered or hit_before, hit_after) if hit_after else None, "improvedQuestionIds": _compare(hit_recovered or hit_before, hit_after)["improvedQuestionIds"] if hit_after else [], "worsenedQuestionIds": _compare(hit_recovered or hit_before, hit_after)["worsenedQuestionIds"] if hit_after else [], "unchangedQuestionIds": _compare(hit_recovered or hit_before, hit_after)["unchangedQuestionIds"] if hit_after else []},
        "annotationOverlay": {"schemaVersion": "review.annotation-overlay.v1", "subjectId": subject_id, "reviewRunId": review_run_id, "annotations": highlights},
        "learnerModelMutation": False,
        "examResultMutation": False,
        "artifactMutation": False,
        "sourceMutation": False,
        "researchErrors": research_errors,
    }
    report["studyGuideMarkdown"] = _markdown(report)
    report["studyGuideHtml"] = _html_section(report)
    return report


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose cross-domain Review Exam Hit enrichment artifacts.")
    parser.add_argument("--hit-before", type=Path, required=True)
    parser.add_argument("--hit-recovered", type=Path)
    parser.add_argument("--hit-after", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--catalog-after", type=Path)
    parser.add_argument("--supplements", type=Path)
    parser.add_argument("--review-run-id", required=True)
    parser.add_argument("--subject-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        supplements = _load(args.supplements) if args.supplements else []
        if not isinstance(supplements, list):
            raise ValueError("supplements must be a list")
        report = compose_hit_review(_load(args.hit_before), review_run_id=args.review_run_id, subject_id=args.subject_id, catalog=_load(args.catalog) if args.catalog else None, hit_recovered=_load(args.hit_recovered) if args.hit_recovered else None, hit_after=_load(args.hit_after) if args.hit_after else None, catalog_after=_load(args.catalog_after) if args.catalog_after else None, supplements=supplements)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "hit-review-report.v1.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.output_dir / "hit-review-annotations.json").write_text(json.dumps(report["annotationOverlay"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.output_dir / "hit-review.md").write_text(report["studyGuideMarkdown"] + "\n", encoding="utf-8")
        (args.output_dir / "hit-review.html").write_text("<!doctype html><html><head><meta charset=\"utf-8\"><style>body{font-family:system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem}.notice{padding:1rem;background:#eef7f3}.hit-card{padding:1rem;margin:1rem 0;border:1px solid #ccd8d2}.hit-card.partial{background:#fffaf0}.hit-card.hit{background:#f2fbf5}mark{background:#fff08a}</style></head><body>" + report["studyGuideHtml"] + "</body></html>\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "gaps": len(report["gaps"]), "highlights": len(report["highlights"]), "researchStatus": report["research"]["status"]}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
