"""Build deterministic, material-only review artifacts.

Material Review consumes a frozen review report, optional Exam Result details,
and an exported canonical material catalog. It never infers learner weakness,
changes mastery, rereads PDFs, or writes Source/Derived content.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "material-review.report.v2"
MATERIAL_REVIEW_MODE = "material"
UNMAPPED = "__unmapped__"
SOURCE_BLOCKERS = {"SOURCE_MISSING", "SOURCE_INCOMPLETE", "QUESTION_UNREADABLE"}
ANSWER_BLOCKERS = {"ANSWER_PROVENANCE_CONFLICT", "REFERENCE_ANSWER_MISSING"}
BLOCKER_ROUTES = {
    "GRAPH_MAPPING_MISSING": "check",
    "GRAPH_MAPPING_AMBIGUOUS": "check",
    "SOURCE_MISSING": "check",
    "SOURCE_INCOMPLETE": "check",
    "QUESTION_UNREADABLE": "check",
    "ANSWER_PROVENANCE_CONFLICT": "amend",
    "REFERENCE_ANSWER_MISSING": "amend",
}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _unique_strings(values: Iterable[Any]) -> list[str]:
    return sorted({value.strip() for value in values if isinstance(value, str) and value.strip()})


def _cards(question: dict[str, Any]) -> list[str]:
    """Return only explicit card IDs; never turn the report placeholder into a card."""

    values: list[Any] = []
    links = question.get("knowledgeLinks", {})
    if isinstance(links, dict):
        values.append(links.get("primaryCardId"))
        values.extend(_list(links.get("secondaryCardIds")))
    values.extend(_list(question.get("knowledgeCardsUsed")))
    values.extend(_list(question.get("selectedCardIds")))
    values.extend(_list(question.get("expectedCards")))
    first_pass = question.get("firstPass", {})
    if isinstance(first_pass, dict):
        values.extend(_list(first_pass.get("knowledgeCardsUsed")))
        retrieval = first_pass.get("retrieval", first_pass.get("retrievalResult", {}))
        if isinstance(retrieval, dict):
            values.extend(_list(retrieval.get("selectedCardIds")))
            values.extend(_list(retrieval.get("matchedCardIds")))
    return _unique_strings(value for value in values if value != UNMAPPED)


def _question_id(question: dict[str, Any]) -> str:
    return _text(question.get("questionId") or question.get("id")) or "unknown-question"


def _answerer_type(review_report: dict[str, Any], exam_result: dict[str, Any] | None) -> str:
    candidates = [
        review_report.get("answererType"),
        (review_report.get("exam") or {}).get("answererType") if isinstance(review_report.get("exam"), dict) else None,
        (exam_result or {}).get("answererType"),
        ((exam_result or {}).get("answerer") or {}).get("type") if isinstance((exam_result or {}).get("answerer"), dict) else None,
    ]
    for candidate in candidates:
        if candidate in {"human", "agent", "model", "unknown"}:
            return candidate
    return "unknown"


def _exam_question_map(exam_result: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(exam_result, dict):
        return {}
    return {_question_id(question): question for question in _list(exam_result.get("questions")) if isinstance(question, dict)}


def _catalog_maps(catalog: dict[str, Any] | None) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[Any]]:
    if not isinstance(catalog, dict):
        return {}, {}, []
    cards = _list(catalog.get("cards", catalog.get("nodes")))
    questions = _list(catalog.get("questions"))
    relations = _list(catalog.get("relations", catalog.get("edges")))
    card_map = {str(item.get("id")): item for item in cards if isinstance(item, dict) and _text(item.get("id"))}
    question_map = {str(item.get("id")): item for item in questions if isinstance(item, dict) and _text(item.get("id"))}
    return card_map, question_map, [item for item in relations if isinstance(item, dict) or isinstance(item, list)]


def _merge_question(review_question: dict[str, Any], exam_question: dict[str, Any] | None, catalog_question: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(review_question)
    if exam_question is not None:
        merged["_exam"] = exam_question
    if catalog_question is not None:
        merged["_catalog"] = catalog_question
    return merged


def _artifact_status(question: dict[str, Any]) -> str:
    return _text(question.get("artifactStatus")) or _text((question.get("sourceMeasurement") or {}).get("artifactStatus")) or "OK"


def _mapping_blocked(question: dict[str, Any]) -> bool:
    # The upstream review report records source and answer conflicts as their
    # own blocking layer. Do not double-count them as graph gaps merely because
    # their placeholder mapping is also empty.
    status = _artifact_status(question)
    if status in SOURCE_BLOCKERS or status in ANSWER_BLOCKERS:
        return False
    if status in {"GRAPH_MAPPING_MISSING", "GRAPH_MAPPING_AMBIGUOUS"}:
        return True
    links = question.get("knowledgeLinks", {})
    if isinstance(links, dict):
        if links.get("mappingStatus") in {"blocked", "ambiguous"}:
            return True
        if links.get("primaryCardId") in {None, "", UNMAPPED}:
            return True
    return not bool(_cards(question))


def _source_blocked(question: dict[str, Any]) -> bool:
    status = _artifact_status(question)
    if status in SOURCE_BLOCKERS:
        return True
    measurement = question.get("sourceMeasurement", {})
    return isinstance(measurement, dict) and measurement.get("retrievalStatus") == "source_issue"


def _answer_conflict(question: dict[str, Any]) -> bool:
    return bool(question.get("answerConflict") is True or _artifact_status(question) in ANSWER_BLOCKERS)


def _outcome(question: dict[str, Any], exam_question: dict[str, Any] | None) -> str:
    value = _text(question.get("observedOutcome"))
    if value:
        return value
    grading = (exam_question or {}).get("grading", {})
    result = grading.get("result") if isinstance(grading, dict) else None
    return {"wrong": "incorrect", "partial": "partially_correct"}.get(result, result or "ungraded")


def _catalog_question_content(question: dict[str, Any]) -> dict[str, Any] | None:
    catalog_question = question.get("_catalog")
    if isinstance(catalog_question, dict) and (_text(catalog_question.get("stem")) or _list(catalog_question.get("options"))):
        return catalog_question
    exam_question = question.get("_exam")
    if isinstance(exam_question, dict) and (_text(exam_question.get("stem")) or _list(exam_question.get("options"))):
        return exam_question
    if _text(question.get("stem")) or _list(question.get("options")):
        return question
    return None


def _solution_status(question: dict[str, Any]) -> str:
    exam_question = question.get("_exam", {})
    official = exam_question.get("official", {}) if isinstance(exam_question, dict) else {}
    if isinstance(official, dict) and _text(official.get("solutionStatus")):
        return official["solutionStatus"]
    catalog_question = question.get("_catalog", {})
    if isinstance(catalog_question, dict) and _text(catalog_question.get("solutionText")):
        return "COMPLETE_NARRATIVE"
    if isinstance(catalog_question, dict) and catalog_question.get("officialAnswer"):
        return "COMPLETE"
    return "UNKNOWN"


def _evidence_tier(question: dict[str, Any], card_ids: list[str]) -> str:
    content = _catalog_question_content(question)
    if _answer_conflict(question):
        return "answer_conflict"
    if _source_blocked(question):
        return "source_blocked"
    if content is not None and card_ids and _solution_status(question) in {"COMPLETE", "COMPLETE_NARRATIVE"}:
        return "complete_material_analysis"
    if content is not None and card_ids:
        return "question_analysis_solution_gap"
    if content is not None and not card_ids:
        return "question_analysis_unmapped"
    if card_ids:
        return "card_backed_material_analysis"
    return "structured_question_missing"


def _evidence_refs(question: dict[str, Any], card: dict[str, Any] | None = None) -> list[str]:
    refs: list[str] = []
    question_id = _question_id(question)
    refs.extend(_list((question.get("diagnosis") or {}).get("evidenceRefs")))
    refs.append(f"review:question:{question_id}")
    exam_question = question.get("_exam", {})
    if isinstance(exam_question, dict):
        exam_page = exam_question.get("examPage", {})
        official = exam_question.get("official", {})
        for label, item in (("exam-page", exam_page), ("official-page", official.get("sourcePage") if isinstance(official, dict) else None)):
            if isinstance(item, dict) and item.get("page") is not None:
                refs.append(f"exam-result:{question_id}:{label}:{item['page']}")
    if card:
        refs.append(f"canonical-card:{card.get('id')}")
        refs.extend(f"source:{ref.get('sourceId')}:{ref.get('locator', '')}" for ref in _list(card.get("sourceRefs")) if isinstance(ref, dict) and _text(ref.get("sourceId")))
    return _unique_strings(refs)


def _relation_parts(relation: Any) -> tuple[str, str, str, str]:
    if isinstance(relation, list) and len(relation) >= 2:
        return str(relation[0]), str(relation[1]), "related", ""
    if isinstance(relation, dict):
        return str(relation.get("from", "")), str(relation.get("to", "")), str(relation.get("type", "related")), str(relation.get("reason", ""))
    return "", "", "related", ""


def _prerequisites(card_id: str, relations: list[Any], cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for relation in relations:
        source, target, relation_type, reason = _relation_parts(relation)
        if target != card_id or source not in cards:
            continue
        result.append({"cardId": source, "title": cards[source].get("title", source), "relationType": relation_type, "reason": reason or "Canonical relation points to this card as a downstream topic."})
    return sorted(result, key=lambda item: (item["cardId"], item["relationType"]))


def _distractors(catalog_question: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not catalog_question:
        return []
    answers = {str(value) for value in _list(catalog_question.get("answer"))}
    result = []
    for option in _list(catalog_question.get("options")):
        if isinstance(option, list) and len(option) >= 2:
            letter, text = str(option[0]), str(option[1])
        elif isinstance(option, dict):
            letter, text = str(option.get("letter", "")), str(option.get("text", ""))
        else:
            continue
        result.append({"option": letter, "text": text, "status": "correct" if letter in answers else "distractor", "basis": "Canonical question record."})
    return result


def _focus_for_card(card_id: str, card: dict[str, Any], questions: list[dict[str, Any]], relations: list[Any], all_question_count: int, card_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    question_ids = sorted({_question_id(question) for question in questions})
    conflicts = sorted({_question_id(question) for question in questions if _answer_conflict(question)})
    content = _list(card.get("explain")) or ([_text(card.get("anchor"))] if _text(card.get("anchor")) else [])
    boundaries = _list(card.get("boundaries"))
    highlights = _list(card.get("highlights"))
    key_statements = _unique_strings(highlights or content)
    linked_questions = []
    for question in questions:
        catalog_question = _catalog_question_content(question)
        if catalog_question is not None:
            linked_questions.append({"questionId": _question_id(question), "type": catalog_question.get("type"), "stem": catalog_question.get("stem", ""), "distractors": _distractors(catalog_question), "scoringPoints": _list(catalog_question.get("shortAnswers")) if catalog_question.get("type") == "分析题" else []})
    prerequisites = _prerequisites(card_id, relations, card_map)
    frequency = len(question_ids)
    return {
        "focusId": f"material-focus-{card_id}",
        "title": card.get("title", card_id),
        "cardId": card_id,
        "group": card.get("group"),
        "importance": {
            "level": "high" if frequency >= 2 else "medium",
            "basis": "mapped_question_frequency",
            "mappedQuestionCount": frequency,
            "totalExamQuestionCount": all_question_count,
            "scope": "mapped_questions_only",
            "coverageWarning": "This is not full-exam frequency because unmapped questions are excluded."
        },
        "questionIds": question_ids,
        "conflictedQuestionIds": conflicts,
        "coreConcept": {"content": content, "provenance": "canonical_card.explain_or_anchor"},
        "keyStatements": {"items": key_statements, "provenance": "canonical_card.highlights_or_explain", "status": "supported" if key_statements else "unavailable"},
        "memorization": {"items": _list(card.get("canonicalExpressions")), "status": "explicit_only", "note": "Only explicitly marked canonical expressions are listed as memorization requirements."},
        "confusions": {"items": boundaries, "provenance": "canonical_card.boundaries"},
        "conditions": {"items": [_text(card.get("method"))] if _text(card.get("method")) else [], "provenance": "canonical_card.method"},
        "distractors": {"items": linked_questions, "status": "supported" if linked_questions else "structured_question_not_available"},
        "scoringPoints": {"items": [point for item in linked_questions for point in item.get("scoringPoints", [])], "status": "supported" if any(item.get("scoringPoints") for item in linked_questions) else "not_available"},
        "prerequisites": prerequisites,
        "sourceRefs": _list(card.get("sourceRefs")),
        "recommendedActions": [
            "先读核心知识，再逐条复述边界。",
            "对照已映射题目核对题干条件；答案冲突题在 amend 完成前不固化为官方答案。",
            "用新的、无提示的变式题验证迁移，不把本次 agent 测量当作用户掌握证据。"
        ],
        "evidenceRefs": _unique_strings(ref for question in questions for ref in _evidence_refs(question, card)),
    }


def _official_answer(question: dict[str, Any], catalog_question: dict[str, Any]) -> str:
    value = catalog_question.get("officialAnswer")
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    if isinstance(value, str) and value.strip():
        return value.strip()
    exam_question = question.get("_exam", {})
    official = exam_question.get("official", {}) if isinstance(exam_question, dict) else {}
    return _text(official.get("answer")) if isinstance(official, dict) else ""


def _option_texts(catalog_question: dict[str, Any], answer: str) -> tuple[list[str], list[str]]:
    correct: list[str] = []
    distractors: list[str] = []
    for option in _list(catalog_question.get("options")):
        if isinstance(option, list) and len(option) >= 2:
            letter, text = str(option[0]), str(option[1])
        elif isinstance(option, dict):
            letter, text = str(option.get("letter", "")), str(option.get("text", ""))
        else:
            continue
        (correct if letter in set(answer) else distractors).append(f"{letter}. {text}")
    return correct, distractors


def _question_analysis(question: dict[str, Any], tier: str) -> dict[str, Any] | None:
    catalog_question = _catalog_question_content(question)
    if catalog_question is None:
        return None
    question_id = _question_id(question)
    card_ids = _cards(question)
    official_answer = _official_answer(question, catalog_question)
    correct_options, distractors = _option_texts(catalog_question, official_answer)
    solution = _text(catalog_question.get("solutionText"))
    if solution:
        core_content = [solution]
        analysis_status = "partial" if _answer_conflict(question) else "complete" if (official_answer or catalog_question.get("type") == "analysis") else "partial"
        explanation_source = "original_pdf_native_text"
    elif correct_options:
        core_content = [f"题目可靠地给出的标准答案选项：{'；'.join(correct_options)}。"]
        analysis_status = "partial"
        explanation_source = "question_and_official_answer_only"
    else:
        core_content = ["题目文本和选项可读，但当前没有足够答案/解析证据固化结论。"]
        analysis_status = "partial"
        explanation_source = "question_text_only"
    source_refs = _evidence_refs(question)
    source_refs.extend(f"material-source:{item.get('sourcePath') or item.get('path')}:{item.get('sourcePage') or item.get('page', '')}" for item in (catalog_question.get("sourceRefs") or []) if isinstance(item, dict) and (item.get("sourcePath") or item.get("path")))
    if catalog_question.get("sourcePath"):
        source_refs.append(f"material-source:{catalog_question['sourcePath']}:{catalog_question.get('sourcePage', '')}")
    return {
        "analysisId": f"material-question-{question_id}",
        "questionId": question_id,
        "year": catalog_question.get("year"),
        "type": catalog_question.get("type"),
        "status": analysis_status,
        "evidenceTier": tier,
        "mappingStatus": "mapped" if card_ids else "unmapped",
        "cardIds": card_ids,
        "stem": _text(catalog_question.get("stem")),
        "options": _list(catalog_question.get("options")),
        "officialAnswer": official_answer or None,
        "answerConflict": _answer_conflict(question),
        "coreKnowledge": {"items": core_content, "provenance": explanation_source},
        "keyStatements": {"items": correct_options, "provenance": "question_option_and_official_answer" if correct_options else "unavailable"},
        "confusions": {"items": distractors, "note": "Distractors are listed as source options; a reason is included only when it appears in the source explanation."},
        "conditions": {"items": [_text(catalog_question.get("stem"))] if _text(catalog_question.get("stem")) else [], "provenance": "original_question_text"},
        "solutionText": solution,
        "sourceRefs": _unique_strings(source_refs),
        "recommendedActions": [
            "先读题干和可靠答案依据，再复述本题要求判断的概念。",
            "逐项对照选项；没有来源解释的干扰项只作为待核对对象，不补写错误理由。",
            "用不同表述的新题进行无提示复测；本条材料分析不改变用户掌握状态。"
        ],
    }


def _flags(question: dict[str, Any], catalog_question: dict[str, Any] | None) -> dict[str, bool]:
    return {
        "GRAPH_MAPPING_MISSING": _mapping_blocked(question),
        "SOURCE_INCOMPLETE": _source_blocked(question),
        "ANSWER_PROVENANCE_CONFLICT": _answer_conflict(question),
        "STRUCTURED_QUESTION_MISSING": catalog_question is None,
        "REFERENCE_ANSWER_MISSING": _solution_status(question) in {"MISSING_FIXED_ANSWER_IN_READABLE_SOURCE", "UNKNOWN"},
    }


def _blocker_analysis(questions: list[dict[str, Any]], all_question_count: int) -> dict[str, Any]:
    flag_sets: dict[str, set[str]] = defaultdict(set)
    for question in questions:
        catalog_question = _catalog_question_content(question)
        for code, present in _flags(question, catalog_question).items():
            if present:
                flag_sets[code].add(_question_id(question))
    original_codes = ["GRAPH_MAPPING_MISSING", "SOURCE_INCOMPLETE", "ANSWER_PROVENANCE_CONFLICT"]
    pairwise = []
    for index, left in enumerate(original_codes):
        for right in original_codes[index + 1:]:
            overlap = flag_sets[left] & flag_sets[right]
            pairwise.append({"codes": [left, right], "questionCount": len(overlap), "questionIds": sorted(overlap)})
    union = set().union(*(flag_sets[code] for code in original_codes)) if original_codes else set()
    root_causes = []
    for code, owner, root_cause, action in (
        ("GRAPH_MAPPING_MISSING", "check → learn", "The frozen Subject graph has no direct canonical primary card for these questions.", "Audit question intake, then create mappings only from reliable Source; never write __unmapped__ to canonical content."),
        ("SOURCE_INCOMPLETE", "check → learn", "Question or fixed-answer provenance is incomplete at the material boundary.", "Preserve the gap, restore the original source evidence, and only then derive a mapping or study point."),
        ("ANSWER_PROVENANCE_CONFLICT", "amend", "A frozen derived answer conflicts with an official answer provenance record.", "Keep both values and send the question to amend/political domain review; do not choose silently."),
    ):
        root_causes.append({"code": code, "questionCount": len(flag_sets[code]), "questionIds": sorted(flag_sets[code]), "repairOwner": owner, "rootCause": root_cause, "repairAction": action, "route": BLOCKER_ROUTES.get(code, "check")})
    return {
        "originalBlockerCounts": {code: len(flag_sets[code]) for code in original_codes},
        "uniqueAffectedQuestionCount": len(union),
        "unaffectedQuestionCount": max(0, all_question_count - len(union)),
        "pairwiseOverlap": pairwise,
        "overlapInterpretation": "Counts are computed from independent flags. A zero pairwise count means the current report records those blockers as disjoint, not that the categories are logically exclusive.",
        "materialInputGaps": [{"code": "STRUCTURED_QUESTION_MISSING", "questionCount": len(flag_sets["STRUCTURED_QUESTION_MISSING"]), "questionIds": sorted(flag_sets["STRUCTURED_QUESTION_MISSING"]), "repairOwner": "learn", "rootCause": "The supplied review/material inputs still have no reliable structured question text/options for these IDs.", "repairAction": "Continue native-text/source intake from reliable material; keep scan or damaged-text pages blocked and do not invent stems, options, or mappings.", "route": "learn"}],
        "referenceAnswerGaps": {"questionCount": len(flag_sets["REFERENCE_ANSWER_MISSING"]), "questionIds": sorted(flag_sets["REFERENCE_ANSWER_MISSING"])},
        "rootCauses": root_causes,
    }


def _unanswered_analysis(questions: list[dict[str, Any]], answerer_type: str) -> dict[str, Any]:
    unanswered = [question for question in questions if _outcome(question, question.get("_exam")) == "unanswered"]
    by_status = Counter(_artifact_status(question) for question in unanswered)
    by_attempt = Counter(_text(question.get("attemptStatus")) or "unknown" for question in unanswered)
    return {
        "count": len(unanswered),
        "questionIds": sorted(_question_id(question) for question in unanswered),
        "byArtifactStatus": dict(sorted(by_status.items())),
        "byAttemptStatus": dict(sorted(by_attempt.items())),
        "answererType": answerer_type,
        "learnerEvidence": False,
        "interpretation": "These unanswered records are not converted into learner failure evidence. With answererType=agent, they represent a closed material/retrieval measurement, not a human first-pass attempt.",
        "doNotBackfillFirstPass": True,
        "nextStep": "If a learner assessment is required, create a new closed-book exam run with a new attemptId set.",
    }


def _learning_tasks(focuses: list[dict[str, Any]], question_analyses: list[dict[str, Any]], blocker_analysis: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = []
    for focus in focuses:
        tasks.append({
            "taskId": f"material-study-{focus['cardId']}",
            "taskType": "material_study",
            "owner": "learn",
            "what": f"Study {focus['title']} from the canonical card.",
            "why": f"It is linked from {focus['importance']['mappedQuestionCount']} reviewed question(s) in the currently mapped subset.",
            "targetCardIds": [focus["cardId"]],
            "questionIds": focus["questionIds"],
            "operations": ["read_core_concept", "contrast_boundaries", "recall_key_statements", "solve_new_variant_without_hints"],
            "dependencies": [item["cardId"] for item in focus.get("prerequisites", [])],
            "evidenceRefs": focus["evidenceRefs"],
            "acceptanceCriteria": ["能用自己的话复述核心判断。", "能说明至少一个易混边界和适用条件。", "在新题上独立作答并通过预先定义的评分标准。"],
            "learnerModelEffect": "none_until_human_retest",
        })
    for analysis in question_analyses:
        tasks.append({
            "taskId": f"material-question-{analysis['questionId']}",
            "taskType": "material_question_study",
            "owner": "learn",
            "what": f"Study the evidence-backed focus in {analysis['questionId']}.",
            "why": "Question-level material is available even when the frozen graph has no primary card." if not analysis["cardIds"] else "Question-level material supplements the linked canonical card.",
            "targetCardIds": analysis["cardIds"],
            "questionIds": [analysis["questionId"]],
            "operations": ["read_question", "compare_answer_evidence", "contrast_distractors", "solve_new_variant_without_hints"],
            "dependencies": analysis["cardIds"],
            "evidenceRefs": analysis["sourceRefs"],
            "acceptanceCriteria": ["能说明题干要求判断的概念或条件。", "能用可靠答案/解析依据解释正确落点。", "在不同表述的新题上独立验证。"],
            "learnerModelEffect": "none_until_human_retest",
        })
    for root in blocker_analysis.get("rootCauses", []):
        if root["questionCount"]:
            tasks.append({
                "taskId": f"repair-{root['code'].lower()}",
                "taskType": "material_repair",
                "owner": root["repairOwner"],
                "what": root["repairAction"],
                "why": root["rootCause"],
                "targetCardIds": [],
                "questionIds": root["questionIds"],
                "operations": ["preserve_source", "classify_root_cause", "rebuild_only_from_reliable_source"],
                "dependencies": [],
                "evidenceRefs": [f"review:blocker:{root['code']}"],
                "acceptanceCriteria": ["修复后重新运行 check/material review；不修改冻结 Exam Result。"],
                "learnerModelEffect": "none",
            })
    return tasks


def _learning_order(focuses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Topologically order focus cards without changing canonical card order."""

    by_id = {focus["cardId"]: focus for focus in focuses}
    dependencies = {
        card_id: {item["cardId"] for item in focus.get("prerequisites", []) if item["cardId"] in by_id}
        for card_id, focus in by_id.items()
    }
    ordered: list[str] = []
    remaining = set(by_id)
    while remaining:
        ready = sorted(card_id for card_id in remaining if dependencies[card_id].issubset(set(ordered)))
        if not ready:
            ready = sorted(remaining)
        ordered.extend(ready)
        remaining.difference_update(ready)
    return [{
        "rank": index,
        "cardId": card_id,
        "title": by_id[card_id]["title"],
        "prerequisiteCardIds": sorted(dependencies[card_id]),
        "reason": "Prerequisites are completed first when they are present in the mapped focus set; this is a review projection, not a canonical reorder."
    } for index, card_id in enumerate(ordered, start=1)]


def _question_learning_order(analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(analyses, key=lambda item: (0 if item["status"] == "complete" else 1, item.get("year") or 9999, item["questionId"]))
    return [{
        "rank": index,
        "analysisId": item["analysisId"],
        "questionId": item["questionId"],
        "cardIds": item["cardIds"],
        "reason": "Complete source-backed analysis first; then work through partial analyses with their evidence gaps visible."
    } for index, item in enumerate(ordered, start=1)]


def _annotation(question: dict[str, Any], review_run_id: str, card_ids: list[str], card_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    question_id = _question_id(question)
    conflict = _answer_conflict(question)
    mapped = bool(card_ids)
    if conflict:
        highlight_type, reason, priority = "confusion", "官方答案与冻结图谱推导存在 provenance 冲突；保留冲突，不把它当作学习者薄弱点。", "high"
    elif mapped:
        highlight_type, reason, priority = "must_practice", "题目已连接到 canonical card，可作为材料学习入口；本标注不表示用户不会。", "medium"
    else:
        highlight_type, reason, priority = "key_source_span", "题目缺少可靠 canonical mapping；先修复材料覆盖，不猜测考点或卡片 ID。", "low"
    content = _catalog_question_content(question)
    # A card mapping does not resolve a question anchor. The question itself
    # needs a structured record; otherwise the overlay must remain actionable
    # but explicitly unresolved.
    resolved = bool(content)
    return {
        "highlightId": f"material-{review_run_id}-{question_id}",
        "subjectId": question.get("subjectId", "") or "unknown",
        "reviewRunId": review_run_id,
        "targetType": "question",
        "targetId": question_id,
        "highlightType": highlight_type,
        "priority": priority,
        "evidenceStrength": "supported" if mapped else "tentative",
        "reason": reason,
        "evidenceRefs": _evidence_refs(question),
        "labels": ["material-review", "no-learner-attribution", "mapped" if mapped else "mapping-gap"],
        "actionHint": "Open the linked question material." if resolved else "Route the question to material intake/check before creating a card link.",
        "renderHint": "highlight",
        "status": "active" if resolved else "unresolved_anchor",
        "anchor": {"status": "resolved", "locator": f"question:{question_id}"} if resolved else {"status": "unresolved", "locator": f"question:{question_id}", "reason": "No structured question record was supplied to Material Review."},
    }


def _card_annotation(focus: dict[str, Any], review_run_id: str, subject_id: str) -> dict[str, Any]:
    return {
        "highlightId": f"material-{review_run_id}-{focus['cardId']}",
        "subjectId": subject_id,
        "reviewRunId": review_run_id,
        "targetType": "card",
        "targetId": focus["cardId"],
        "highlightType": "high_frequency" if focus["importance"]["mappedQuestionCount"] >= 2 else "must_understand",
        "priority": focus["importance"]["level"],
        "evidenceStrength": "supported",
        "reason": "Canonical card content is linked by the mapped question subset; frequency is explicitly partial, not a full-exam frequency claim.",
        "evidenceRefs": focus["evidenceRefs"],
        "labels": ["material-review", "no-learner-attribution", "canonical-card"],
        "actionHint": "Read the card, its boundaries, and its linked questions.",
        "renderHint": "highlight",
        "status": "active",
        "anchor": {"status": "resolved", "locator": f"card:{focus['cardId']}"},
    }


def _markdown(report: dict[str, Any]) -> str:
    coverage = report["coverage"]
    lines = [
        f"# Material Review: {report['subjectId']}",
        "",
        "> This is a material-only review. It does not update the user's Learner Model and does not modify the frozen Exam Result or canonical learning artifact.",
        "",
        "## Executive summary",
        "",
        f"- Exam questions: **{coverage['totalQuestionCount']}**",
        f"- Card-backed material focuses: **{coverage['cardBackedQuestionCount']} questions / {coverage['focusCardCount']} cards**",
        f"- Complete question-level material analyses: **{coverage['questionAnalysisProducedCount']}**",
        f"- Unanswered records: **{report['unansweredAnalysis']['count']}**; learner attribution: **none**",
        f"- Original blocker union: **{report['blockerAnalysis']['uniqueAffectedQuestionCount']} unique questions**",
        "",
        "## Review focus",
        "",
    ]
    if not report["focuses"]:
        lines.append("No card-backed material focus was available from the supplied canonical catalog.")
    for index, focus in enumerate(report["focuses"], start=1):
        links = ", ".join(f"[{question_id}](#question-{question_id})" for question_id in focus["questionIds"]) or "none"
        lines.extend([f"### {index}. {focus['title']}", f"- Card: `{focus['cardId']}`", f"- Importance: `{focus['importance']['level']}` — {focus['importance']['mappedQuestionCount']} mapped question(s); **mapped subset only**.", f"- Questions: {links}", "- Core knowledge:"])
        lines.extend(f"  - {item}" for item in focus["coreConcept"]["content"])
        lines.append("- Key statements:")
        lines.extend(f"  - {item}" for item in focus["keyStatements"]["items"])
        lines.append("- Confusions and boundaries:")
        lines.extend(f"  - {item}" for item in focus["confusions"]["items"])
        lines.append("- Conditions and judgement operation:")
        lines.extend(f"  - {item}" for item in focus["conditions"]["items"])
        if focus["prerequisites"]:
            lines.append("- Prerequisites:")
            lines.extend(f"  - `{item['cardId']}` {item['title']}: {item['reason']}" for item in focus["prerequisites"])
        lines.append("- Recommended action: read the card, contrast the boundary, then solve a new no-hint variant.")
        lines.append(f"- Sources: {', '.join(focus['evidenceRefs'])}")
        lines.append("")
    lines.extend(["## Question-level material analyses", ""])
    if not report["questionAnalyses"]:
        lines.append("No structured question material was available.")
    for analysis in report["questionAnalyses"]:
        card_links = ", ".join(f"`{card_id}`" for card_id in analysis["cardIds"]) or "unmapped"
        lines.extend([f"### {analysis['questionId']}", f"- Evidence status: `{analysis['status']}`; mapping: `{analysis['mappingStatus']}`; cards: {card_links}", f"- Question: {analysis['stem']}"])
        if analysis["officialAnswer"]:
            lines.append(f"- Official answer evidence: `{analysis['officialAnswer']}`")
        lines.append("- Core knowledge:")
        lines.extend(f"  - {item}" for item in analysis["coreKnowledge"]["items"])
        if analysis["keyStatements"]["items"]:
            lines.append("- Key statements:")
            lines.extend(f"  - {item}" for item in analysis["keyStatements"]["items"])
        if analysis["confusions"]["items"]:
            lines.append("- Options requiring comparison:")
            lines.extend(f"  - {item}" for item in analysis["confusions"]["items"])
        lines.append("- Recommended action: read the evidence, compare options, and solve a new variant without hints.")
        lines.append(f"- Sources: {', '.join(analysis['sourceRefs'])}")
        lines.append("")
    lines.extend(["## Recommended study order", ""])
    for item in report["learningOrder"]:
        prerequisites = ", ".join(f"`{card_id}`" for card_id in item["prerequisiteCardIds"]) or "none"
        lines.append(f"{item['rank']}. [{item['title']}](#card-{item['cardId']}) — prerequisites: {prerequisites}")
    lines.extend(["", "## Blockers and repair routes", "", f"Unique affected questions: **{report['blockerAnalysis']['uniqueAffectedQuestionCount']}**.", ""])
    for item in report["blockerAnalysis"]["rootCauses"] + report["blockerAnalysis"]["materialInputGaps"]:
        lines.extend([f"### `{item['code']}` — {item['questionCount']} question(s)", f"- Root cause: {item['rootCause']}", f"- Repair owner: `{item['repairOwner']}`", f"- Action: {item['repairAction']}", ""])
    lines.extend(["## Unanswered records", "", f"There are **{report['unansweredAnalysis']['count']}** unanswered records. They remain unanswered; they are not backfilled as learner mistakes. {report['unansweredAnalysis']['nextStep']}", "", "## Learner Model boundary", "", "Material Review wrote **0** observations, **0** mastery changes, and **0** self-reports.", ""])
    return "\n".join(lines)


def _html(report: dict[str, Any]) -> str:
    def esc(value: Any) -> str:
        return html.escape(str(value), quote=True)

    blocks = [f"<h1>Material Review: {esc(report['subjectId'])}</h1><p class=\"notice\">Material-only output. Learner Model, Exam Result, Source, and canonical content were not modified.</p>"]
    coverage = report["coverage"]
    blocks.append("<section id=\"summary\"><h2>Executive summary</h2><ul>" + "".join([
        f"<li>Exam questions: <strong>{coverage['totalQuestionCount']}</strong></li>",
        f"<li>Card-backed focuses: <strong>{coverage['cardBackedQuestionCount']}</strong> questions / <strong>{coverage['focusCardCount']}</strong> cards</li>",
        f"<li>Question-level analyses: <strong>{coverage['questionAnalysisProducedCount']}</strong> ({coverage['completeQuestionAnalysisCount']} complete, {coverage['partialQuestionAnalysisCount']} partial)</li>",
        f"<li>Unanswered records: <strong>{report['unansweredAnalysis']['count']}</strong>; learner attribution: none</li>",
    ]) + "</ul></section>")
    focus_html = []
    for focus in report["focuses"]:
        question_links = " ".join(f"<a href=\"#question-{esc(qid)}\">{esc(qid)}</a>" for qid in focus["questionIds"]) or "none"
        focus_html.append(f"<article class=\"focus\" id=\"card-{esc(focus['cardId'])}\"><h3>{esc(focus['title'])}</h3><p><code>{esc(focus['cardId'])}</code> · importance {esc(focus['importance']['level'])} · mapped subset count {focus['importance']['mappedQuestionCount']}</p><p>Questions: {question_links}</p><h4>Core knowledge</h4><ul>{''.join(f'<li>{esc(item)}</li>' for item in focus['coreConcept']['content'])}</ul><h4>Key statements</h4><ul>{''.join(f'<li>{esc(item)}</li>' for item in focus['keyStatements']['items'])}</ul><h4>Confusions and boundaries</h4><ul>{''.join(f'<li>{esc(item)}</li>' for item in focus['confusions']['items'])}</ul><h4>Conditions</h4><ul>{''.join(f'<li>{esc(item)}</li>' for item in focus['conditions']['items'])}</ul></article>")
    blocks.append("<section id=\"focus\"><h2>Review focus</h2>" + ("".join(focus_html) or "<p>No card-backed focus.</p>") + "</section>")
    analysis_html = []
    for analysis in report["questionAnalyses"]:
        card_links = " ".join(f"<a href=\"#card-{esc(card_id)}\">{esc(card_id)}</a>" for card_id in analysis["cardIds"]) or "unmapped"
        options = "".join(f"<li>{esc(option.get('letter', ''))}. {esc(option.get('text', ''))}</li>" for option in analysis["options"] if isinstance(option, dict))
        core = "".join(f"<p>{esc(item)}</p>" for item in analysis["coreKnowledge"]["items"])
        key_statements = "".join(f"<li>{esc(item)}</li>" for item in analysis["keyStatements"]["items"])
        confusions = "".join(f"<li>{esc(item)}</li>" for item in analysis["confusions"]["items"])
        answer = f"<p><strong>Official answer evidence:</strong> <code>{esc(analysis['officialAnswer'])}</code></p>" if analysis["officialAnswer"] else "<p>No fixed official answer was supplied.</p>"
        analysis_html.append(f"<article class=\"question-analysis\" id=\"analysis-{esc(analysis['questionId'])}\"><h3>{esc(analysis['questionId'])}</h3><p>Status: <code>{esc(analysis['status'])}</code> · mapping: <code>{esc(analysis['mappingStatus'])}</code> · cards: {card_links}</p><h4>Question</h4><p>{esc(analysis['stem'])}</p><ul>{options}</ul>{answer}<h4>Core knowledge</h4>{core}<h4>Key statements</h4><ul>{key_statements or '<li>Not separately marked in the supplied source.</li>'}</ul><h4>Confusions and conditions</h4><ul>{confusions or '<li>No source-backed distractor explanation was available.</li>'}</ul><h4>Source solution</h4><p>{esc(analysis['solutionText'] or 'No native-text solution was available; this analysis remains partial.')}</p></article>")
    blocks.append("<section id=\"question-analyses\"><h2>Question-level material analyses</h2>" + ("".join(analysis_html) or "<p>No structured question material.</p>") + "</section>")
    rows = []
    for item in report["blockerAnalysis"]["rootCauses"] + report["blockerAnalysis"]["materialInputGaps"]:
        rows.append(f"<tr><td><code>{esc(item['code'])}</code></td><td>{item['questionCount']}</td><td>{esc(item['repairOwner'])}</td><td>{esc(item['rootCause'])}</td></tr>")
    order_html = "".join(f"<li><a href=\"#card-{esc(item['cardId'])}\">{esc(item['title'])}</a> — prerequisites: {esc(', '.join(item['prerequisiteCardIds']) or 'none')}</li>" for item in report["learningOrder"])
    blocks.append(f"<section id=\"order\"><h2>Recommended study order</h2><ol>{order_html}</ol></section>")
    blocks.append(f"<section id=\"blockers\"><h2>Blockers and routes</h2><p>Unique affected questions: <strong>{report['blockerAnalysis']['uniqueAffectedQuestionCount']}</strong></p><table><thead><tr><th>Code</th><th>Questions</th><th>Owner</th><th>Root cause</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>")
    question_rows = []
    for question in report["questionIndex"]:
        links = " ".join(f"<a href=\"#card-{esc(card_id)}\">{esc(card_id)}</a>" for card_id in question["cardIds"]) or "unmapped"
        question_rows.append(f"<article class=\"question\" id=\"question-{esc(question['questionId'])}\"><h3>{esc(question['questionId'])}</h3><p>Outcome: <code>{esc(question['outcome'])}</code> · evidence tier: <code>{esc(question['evidenceTier'])}</code></p><p>Cards: {links}</p><p>{esc(question['materialNote'])}</p></article>")
    blocks.append("<section id=\"questions\"><h2>Question index</h2>" + "".join(question_rows) + "</section>")
    return "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Material Review</title><style>body{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;line-height:1.6;color:#17211f}.notice{background:#eef7f3;padding:1rem;border-left:4px solid #2c7a62}.focus,.question,.question-analysis{border:1px solid #d7e2de;border-radius:10px;padding:1rem;margin:1rem 0}.focus{background:#fbfdfc}.question-analysis{background:#fffdf7}table{border-collapse:collapse;width:100%}th,td{border:1px solid #d7e2de;padding:.5rem;text-align:left}code{background:#f1f4f3;padding:.1rem .25rem;border-radius:4px}a{color:#116b55}</style></head><body>" + "".join(blocks) + "</body></html>"


def build_material_review(review_report: dict[str, Any], review_run_id: str | None = None, *, exam_result: dict[str, Any] | None = None, catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a material review from either review.report.v2 or legacy exam input."""

    # Keep the earlier small API useful for callers that pass an Exam Result directly.
    if review_report.get("schemaVersion") != "review.report.v2" and review_report.get("status") == "CLOSED":
        legacy_exam = review_report
        review_report = {
            "schemaVersion": "review.report.v2",
            "reviewRunId": review_run_id or "material-review-legacy",
            "exam": {"examRunId": legacy_exam.get("examRunId"), "subjectId": legacy_exam.get("subjectId"), "answererType": ((legacy_exam.get("answerer") or {}).get("type") if isinstance(legacy_exam.get("answerer"), dict) else "unknown")},
            "questions": legacy_exam.get("questions", []),
        }
        exam_result = legacy_exam
    review_run_id = review_run_id or _text(review_report.get("reviewRunId")) or "material-review"
    exam = review_report.get("exam", {}) if isinstance(review_report.get("exam"), dict) else {}
    exam_questions = _exam_question_map(exam_result)
    card_map, catalog_question_map, relations = _catalog_maps(catalog)
    raw_questions = [question for question in _list(review_report.get("questions")) if isinstance(question, dict)]
    questions = []
    for raw_question in raw_questions:
        question_id = _question_id(raw_question)
        questions.append(_merge_question(raw_question, exam_questions.get(question_id), catalog_question_map.get(question_id)))
    if not questions and exam_result:
        questions = [dict(question) for question in _list(exam_result.get("questions")) if isinstance(question, dict)]
    answerer_type = _answerer_type(review_report, exam_result)
    subject_id = _text(review_report.get("subjectId")) or _text(exam.get("subjectId")) or _text((exam_result or {}).get("subjectId")) or "unknown"
    exam_run_id = _text(review_report.get("examRunId")) or _text(exam.get("examRunId")) or _text((exam_result or {}).get("examRunId")) or "unknown-exam"
    focuses = []
    card_questions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    question_index = []
    question_analyses: list[dict[str, Any]] = []
    evidence_counts = Counter()
    for question in questions:
        card_ids = _cards(question)
        for card_id in card_ids:
            card_questions[card_id].append(question)
        catalog_question = _catalog_question_content(question)
        tier = _evidence_tier(question, card_ids)
        evidence_counts[tier] += 1
        analysis = _question_analysis(question, tier)
        if analysis is not None:
            question_analyses.append(analysis)
        question_index.append({
            "questionId": _question_id(question),
            "outcome": _outcome(question, question.get("_exam")),
            "cardIds": card_ids,
            "evidenceTier": tier,
            "analysisId": analysis.get("analysisId") if analysis else None,
            "hasMaterialContent": analysis is not None,
            "materialNote": "Structured question content is available." if catalog_question else "Question text/options are not in the supplied structured material catalog; no question-level content is invented.",
            "evidenceRefs": _evidence_refs(question),
        })
    for card_id in sorted(card_questions):
        card = card_map.get(card_id)
        if card is not None:
            focuses.append(_focus_for_card(card_id, card, card_questions[card_id], relations, len(questions), card_map))
    blocker_analysis = _blocker_analysis(questions, len(questions))
    annotations = [_card_annotation(focus, review_run_id, subject_id) for focus in focuses]
    for question in questions:
        annotations.append(_annotation(question, review_run_id, _cards(question), card_map))
    exam_meta = exam_result or {}
    snapshot = exam_meta.get("snapshot", {}) if isinstance(exam_meta, dict) else {}
    exam_hash = _text(exam.get("examResultHashBefore")) or _text(exam.get("examResultHash"))
    report = {
        "schemaVersion": SCHEMA_VERSION,
        "reviewMode": MATERIAL_REVIEW_MODE,
        "reviewRunId": review_run_id,
        "examRunId": exam_run_id,
        "subjectId": subject_id,
        "answererType": answerer_type,
        "learnerModelWriteAllowed": False,
        "learnerModelMutation": False,
        "examResultMutation": False,
        "artifactMutation": False,
        "sourceMutation": False,
        "source": "review_report_and_closed_exam_result",
        "inputIdentity": {
            "reviewReportSchemaVersion": review_report.get("schemaVersion"),
            "examResultSchemaVersion": exam_meta.get("schemaVersion"),
            "examResultPath": _text(exam.get("resultPath")),
            "artifactVersion": _text(exam.get("artifactVersion")) or _text(snapshot.get("artifactVersion")),
            "artifactHash": _text(exam.get("artifactHash")) or _text(snapshot.get("artifactHash")),
            "materialCatalogSchemaVersion": catalog.get("schemaVersion") if isinstance(catalog, dict) else None,
            "materialSourcePolicy": catalog.get("sourcePolicy") if isinstance(catalog, dict) else None,
            "materialSourceStats": catalog.get("materialSourceStats") if isinstance(catalog, dict) else None,
            "examResultHashBefore": exam_hash,
            "examResultHashAfter": exam_hash,
        },
        "coverage": {
            "totalQuestionCount": len(questions),
            "focusCardCount": len(focuses),
            "cardBackedQuestionCount": sum(1 for question in questions if _cards(question)),
            "questionAnalysisProducedCount": len(question_analyses),
            "completeQuestionAnalysisCount": sum(item["status"] == "complete" for item in question_analyses),
            "partialQuestionAnalysisCount": sum(item["status"] == "partial" for item in question_analyses),
            "questionAnalysisUnmappedCount": evidence_counts["question_analysis_unmapped"],
            "cardBackedOnlyCount": evidence_counts["card_backed_material_analysis"],
            "answerConflictCount": evidence_counts["answer_conflict"],
            "sourceBlockedCount": evidence_counts["source_blocked"],
            "structuredQuestionMissingCount": sum(1 for question in questions if _catalog_question_content(question) is None),
            "evidenceLevels": dict(sorted(evidence_counts.items())),
            "frequencyBasis": "mapped_question_subset",
            "coverageWarning": "No frequency or importance claim includes unmapped questions.",
        },
        "blockerAnalysis": blocker_analysis,
        "unansweredAnalysis": _unanswered_analysis(questions, answerer_type),
        "focuses": focuses,
        "questionAnalyses": sorted(question_analyses, key=lambda item: item["questionId"]),
        "questionIndex": sorted(question_index, key=lambda item: item["questionId"]),
        "annotations": annotations,
        "learningOrder": [],
        "questionLearningOrder": [],
        "learningTasks": _learning_tasks(focuses, question_analyses, blocker_analysis),
        "retestPlans": [],
        "routes": sorted({root["route"] for root in blocker_analysis["rootCauses"] if root["questionCount"]} | ({"learn"} if blocker_analysis["materialInputGaps"][0]["questionCount"] else set())),
        "learnerModel": {"writeAllowed": False, "mutation": False, "observationsAppended": 0, "masteryChanges": 0, "selfReportChanges": 0, "reason": "Material Review is not learner assessment; agent performance and material gaps are not user evidence."},
        "annotationOverlay": {"schemaVersion": "review.annotation-overlay.v1", "subjectId": subject_id, "reviewRunId": review_run_id, "annotations": annotations},
        "examResultIntegrity": {"hashBefore": exam_hash, "hashAfter": exam_hash, "unchanged": True, "mutation": False},
    }
    report["learningOrder"] = _learning_order(focuses)
    report["questionLearningOrder"] = _question_learning_order(question_analyses)
    report["studyGuideMarkdown"] = _markdown(report)
    report["studyGuideHtml"] = _html(report)
    return report


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a material-only review from a frozen review report.")
    parser.add_argument("--review-report", type=Path, required=True)
    parser.add_argument("--exam-result", type=Path)
    parser.add_argument("--catalog", type=Path, help="Exported canonical card/question/relation catalog.")
    parser.add_argument("--exam-hit-before", "--exam-hit", dest="exam_hit_before", type=Path, help="Full exam.hit.report.v1 produced from the original frozen graph snapshot.")
    parser.add_argument("--exam-hit-after", dest="exam_hit_after", type=Path, help="Optional recheck report from the enriched graph snapshot.")
    parser.add_argument("--catalog-after", type=Path, help="Optional catalog from the enriched graph snapshot.")
    parser.add_argument("--supplements", type=Path, help="Validated External Supplement records returned by the research stage.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--review-run-id")
    args = parser.parse_args()
    try:
        review_report = _load_json(args.review_report)
        exam_result = _load_json(args.exam_result) if args.exam_result else None
        catalog = _load_json(args.catalog) if args.catalog else None
        before_hash = _sha256(args.exam_result) if args.exam_result else ""
        report = build_material_review(review_report, args.review_run_id, exam_result=exam_result, catalog=catalog)
        after_hash = _sha256(args.exam_result) if args.exam_result else before_hash
        report["inputIdentity"]["examResultHashBefore"] = before_hash or report["inputIdentity"].get("examResultHashBefore", "")
        report["inputIdentity"]["examResultHashAfter"] = after_hash or report["inputIdentity"].get("examResultHashAfter", "")
        report["examResultIntegrity"] = {"hashBefore": before_hash, "hashAfter": after_hash, "unchanged": before_hash == after_hash, "mutation": before_hash != after_hash}
        report["examResultMutation"] = before_hash != after_hash
        report["studyGuideMarkdown"] = _markdown(report)
        report["studyGuideHtml"] = _html(report)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        hit_review = None
        if args.exam_hit_before:
            from compose_hit_review import compose_hit_review

            supplements = _load_json(args.supplements) if args.supplements else []
            if not isinstance(supplements, list):
                raise ValueError("--supplements must contain a JSON list")
            hit_review = compose_hit_review(
                _load_json(args.exam_hit_before),
                review_run_id=args.review_run_id or report["reviewRunId"],
                subject_id=report["subjectId"],
                catalog=catalog,
                hit_after=_load_json(args.exam_hit_after) if args.exam_hit_after else None,
                catalog_after=_load_json(args.catalog_after) if args.catalog_after else None,
                supplements=supplements,
            )
            report["examHitReview"] = hit_review
            report["annotationOverlay"]["annotations"].extend(hit_review["annotationOverlay"]["annotations"])
            report["studyGuideMarkdown"] += "\n\n" + hit_review["studyGuideMarkdown"]
            report["studyGuideHtml"] = report["studyGuideHtml"].replace("</body>", hit_review["studyGuideHtml"] + "</body>")
            (args.output_dir / "hit-review-report.v1.json").write_text(json.dumps(hit_review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (args.output_dir / "hit-review-annotations.json").write_text(json.dumps(hit_review["annotationOverlay"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (args.output_dir / "hit-review.md").write_text(hit_review["studyGuideMarkdown"] + "\n", encoding="utf-8")
            (args.output_dir / "hit-review.html").write_text("<!doctype html><html><head><meta charset=\"utf-8\"><style>body{font-family:system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem}.notice{padding:1rem;background:#eef7f3}.hit-card{padding:1rem;margin:1rem 0;border:1px solid #ccd8d2}.hit-card.partial{background:#fffaf0}.hit-card.hit{background:#f2fbf5}mark{background:#fff08a}</style></head><body>" + hit_review["studyGuideHtml"] + "</body></html>\n", encoding="utf-8")
        (args.output_dir / "material-review-report.v2.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.output_dir / "material-review-annotations.json").write_text(json.dumps(report["annotationOverlay"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.output_dir / "material-review.md").write_text(report["studyGuideMarkdown"] + "\n", encoding="utf-8")
        (args.output_dir / "material-review.html").write_text(report["studyGuideHtml"] + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "outputDir": str(args.output_dir), "focusCards": len(report["focuses"]), "questionAnalysisProduced": report["coverage"]["questionAnalysisProducedCount"], "uniqueAffectedQuestions": report["blockerAnalysis"]["uniqueAffectedQuestionCount"], "examHitHighlights": len(hit_review["highlights"]) if hit_review else 0, "examHitGaps": len(hit_review["gaps"]) if hit_review else 0, "examResultUnchanged": report["examResultIntegrity"]["unchanged"]}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
