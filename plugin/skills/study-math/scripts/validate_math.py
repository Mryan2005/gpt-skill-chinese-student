"""Validate structured mathematics records at the JSON boundary.

The validator deliberately keeps domain checks in one pure module.  The CLI
only loads JSON, prints a deterministic report, and returns a non-zero status
when the record cannot be used as an exam-ready source for the math graph.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


CARD_TYPES = {
    "definition",
    "theorem",
    "formula",
    "method",
    "problem-pattern",
    "comparison",
    "bridge",
}

ENTITY_TYPES = {
    "chapter_metadata",
    "knowledge_content",
    "question",
    "solution",
    "answer",
    "answer_key",
    "formula",
    "figure",
    "example",
    "note",
    "question_group",
    "unclassified",
}

METADATA_ENTITY_TYPES = {"chapter_metadata", "question_group", "unclassified"}
RELATION_TYPES = {
    "prerequisite",
    "derives",
    "implies",
    "equivalent",
    "special_case",
    "generalization",
    "part_of",
    "method_for",
    "used_by",
    "alternative",
    "contrast",
    "often_confused",
}
QUESTION_TYPES = {
    "multiple_choice",
    "single_choice",
    "multiple_select",
    "fill_in",
    "calculation",
    "proof",
    "short_answer",
    "comprehensive",
}
STATUS_VALUES = {
    "COMPLETE",
    "QUESTION_INCOMPLETE",
    "SOLUTION_INCOMPLETE",
    "DERIVED_COMPLETE",
    "OFFICIAL_COMPLETE",
    "HISTORICAL_COMPLETE",
    "ANSWER_MISSING",
    "ANSWER_UNVERIFIED",
    "ANSWER_VERIFIED",
    "DERIVED_VERIFIED",
    "CONFLICTING",
}
ANSWER_EVIDENCE_KINDS = {"official_answer", "historical_answer", "derived_answer"}
SOLUTION_EVIDENCE_KINDS = {"official_solution", "historical_solution", "derived_solution"}

TYPE_FIELDS = {
    "definition": ("definition", "domain", "contrasts"),
    "theorem": ("preconditions", "conclusion", "conditionRoles", "failureConditions"),
    "formula": ("formulae", "variables", "conditions"),
    "method": ("signals", "steps", "stopRule", "failureConditions"),
    "problem-pattern": (
        "recognitionSignals",
        "firstStep",
        "decisionTree",
        "closingChecks",
    ),
    "comparison": ("compares", "dimensions", "conclusion"),
    "bridge": ("decisionQuestion", "branches", "outgoingRelationIds"),
}

GENERIC_RELATION_REASONS = {
    "a和b有关系",
    "二者有关系",
    "有关系",
    "应放在同一条知识链中",
    "相关",
}

INCOMPLETE_SOLUTION_PATTERNS = (
    re.compile(r"_{3,}"),
    re.compile(r"由\s*(?:得|可得)"),
    re.compile(r"代入\s*(?:得|可得)"),
    re.compile(r"(?:解析|证明|计算)\s*(?:略|见下|待补)"),
)


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    message: str
    severity: str = "error"


@dataclass
class ValidationReport:
    issues: list[Issue] = field(default_factory=list)
    metrics: dict[str, float | int] = field(default_factory=dict)
    counts: Counter[str] = field(default_factory=Counter)

    def add(self, code: str, path: str, message: str, severity: str = "error") -> None:
        issue = Issue(code=code, path=path, message=message, severity=severity)
        self.issues.append(issue)
        self.counts[code] += 1

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def passed(self) -> bool:
        return not self.errors


def _path(base: str, key: str | int) -> str:
    return f"{base}.{key}" if base else str(key)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _meaningful(value: Any) -> bool:
    if _non_empty_text(value):
        return True
    if isinstance(value, dict):
        return any(_meaningful(item) for item in value.values())
    if isinstance(value, list):
        return any(_meaningful(item) for item in value)
    return False


def _normalize(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{key}:{_normalize(value[key])}" for key in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_normalize(item) for item in value) + "]"
    if value is None:
        return ""
    text = str(value).strip().lower()
    return re.sub(r"\s+", " ", text)


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_normalize(value).encode("utf-8")).hexdigest()


def _index_by_id(
    records: Iterable[Any],
    name: str,
    report: ValidationReport,
    missing_code: str | None = None,
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        path = f"{name}[{index}]"
        if not isinstance(record, dict):
            report.add("SCHEMA_RECORD_NOT_OBJECT", path, "record must be an object")
            continue
        record_id = record.get("id")
        if not _non_empty_text(record_id):
            report.add(missing_code or "ID_MISSING", f"{path}.id", "stable id is required")
            continue
        if record_id in indexed:
            duplicate_code = "QUESTION_ID_DUPLICATE" if name == "questions" else f"{name.upper()}_ID_DUPLICATE"
            report.add(duplicate_code, f"{path}.id", f"duplicate id: {record_id}")
            continue
        indexed[record_id] = record
    return indexed


def _collect_math_object_ids(value: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(value, dict):
        if value.get("kind") == "math" and _non_empty_text(value.get("mathObjectId")):
            ids.add(value["mathObjectId"])
        for child in value.values():
            ids.update(_collect_math_object_ids(child))
    elif isinstance(value, list):
        for child in value:
            ids.update(_collect_math_object_ids(child))
    return ids


def _option_has_content(value: Any) -> bool:
    if isinstance(value, dict) and value.get("kind") == "math":
        return _non_empty_text(value.get("mathObjectId"))
    return _meaningful(value)


def _question_source_ids(question: dict[str, Any]) -> set[str]:
    source_ids = set(_as_list(question.get("sourceIds")))
    if _non_empty_text(question.get("sourceId")):
        source_ids.add(question["sourceId"])
    return {item for item in source_ids if isinstance(item, str)}


def _relation_reason_is_valid(reason: Any) -> bool:
    if not _non_empty_text(reason):
        return False
    normalized = re.sub(r"\s+", "", reason.lower())
    return len(normalized) >= 9 and normalized not in GENERIC_RELATION_REASONS


def _expected_question_key(value: Any) -> tuple[Any, Any] | None:
    if isinstance(value, dict):
        number = value.get("originalNumber", value.get("number"))
        question_type = value.get("type")
        if number is not None or question_type is not None:
            return number, question_type
    return None


def _actual_question_identity(question: dict[str, Any]) -> tuple[Any, Any]:
    return question.get("originalNumber"), question.get("type")


def _validate_top_level(record: dict[str, Any], report: ValidationReport) -> None:
    required = ("modules", "cards", "questions", "relations", "sources", "progress")
    for key in required:
        if key not in record:
            report.add("SCHEMA_MISSING_FIELD", key, "top-level collection is required")
        elif not isinstance(record[key], list | dict):
            report.add("SCHEMA_WRONG_TYPE", key, "top-level collection has the wrong type")


def _validate_modules(
    modules: dict[str, dict[str, Any]],
    cards: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> None:
    valid_parents = set(modules) | set(cards)
    for module_id, module in modules.items():
        path = f"modules[{module_id}]"
        if not _non_empty_text(module.get("title")):
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.title", "module title is required")
        parent_id = module.get("parentId")
        if parent_id is not None and parent_id not in valid_parents:
            report.add("RELATION_DANGLING", f"{path}.parentId", f"unknown parent: {parent_id}")
        for source_id in _as_list(module.get("sourceIds")):
            if source_id not in sources:
                report.add("SOURCE_DANGLING", f"{path}.sourceIds", f"unknown source: {source_id}")


def _validate_cards(
    cards: dict[str, dict[str, Any]],
    modules: dict[str, dict[str, Any]],
    questions: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    relations: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> None:
    size_violations = 0
    atomic_cards = 0
    for card_id, card in cards.items():
        path = f"cards[{card_id}]"
        card_type = card.get("type")
        if card_type not in CARD_TYPES:
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.type", f"unknown card type: {card_type}")
            continue

        for field_name in ("moduleId", "title", "recallPrompt", "sourceIds", "questionIds", "operationTags"):
            if field_name not in card:
                report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.{field_name}", "required card field is missing")
        module_id = card.get("moduleId")
        if module_id not in modules and module_id not in cards:
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.moduleId", f"unknown module/card: {module_id}")
        parent_id = card.get("parentId")
        if parent_id is not None and parent_id not in modules and parent_id not in cards:
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.parentId", f"unknown parent: {parent_id}")

        for field_name in TYPE_FIELDS[card_type]:
            if field_name not in card or not _meaningful(card[field_name]):
                report.add(
                    "DOMAIN_TEMPLATE_MISMATCH",
                    f"{path}.{field_name}",
                    f"{card_type} card requires {field_name}",
                )

        atomicity = card.get("atomicity")
        if not isinstance(atomicity, dict):
            report.add("CARD_NOT_ATOMIC", f"{path}.atomicity", "atomicity object is required")
        else:
            core_question = atomicity.get("coreQuestion")
            task_count = atomicity.get("independentRecallTasks")
            split_candidates = atomicity.get("splitCandidates", [])
            if not _non_empty_text(core_question) or task_count != 1:
                report.add(
                    "CARD_NOT_ATOMIC",
                    f"{path}.atomicity",
                    "one non-empty coreQuestion and independentRecallTasks=1 are required",
                )
            elif not split_candidates:
                atomic_cards += 1
            if split_candidates:
                report.add(
                    "CARD_NOT_ATOMIC",
                    f"{path}.atomicity.splitCandidates",
                    "card still contains independent split candidates",
                )

        formula_count = len(_as_list(card.get("formulae")))
        step_count = len(_as_list(card.get("steps")))
        pitfall_count = len(_as_list(card.get("pitfalls")))
        recommended_count = len(_as_list(card.get("recommendedQuestionIds")))
        if formula_count > 3 or step_count > 7 or pitfall_count > 5 or recommended_count > 3:
            size_violations += 1
            report.add(
                "CARD_TOO_LARGE",
                path,
                "formulae>3, steps>7, pitfalls>5, or recommendedQuestionIds>3",
            )
        if len(_as_list(card.get("scopeConcepts"))) > 3:
            report.add("CARD_TOO_BROAD", f"{path}.scopeConcepts", "card spans too many independent concepts")

        if card_type == "bridge" and not _as_list(card.get("outgoingRelationIds")):
            report.add("EMPTY_BRIDGE", path, "bridge must declare outgoingRelationIds")

        forbidden_question_fields = {"questions", "fullQuestions", "questionTexts", "copiedQuestionStems"}
        leaked = forbidden_question_fields & set(card)
        if leaked:
            report.add(
                "DOMAIN_TEMPLATE_MISMATCH",
                path,
                f"card copies full question content; use questionIds only: {sorted(leaked)}",
            )

        for source_id in _as_list(card.get("sourceIds")):
            if source_id not in sources:
                report.add("SOURCE_DANGLING", f"{path}.sourceIds", f"unknown source: {source_id}")
        for question_id in _as_list(card.get("questionIds")):
            if question_id not in questions:
                report.add("QUESTION_DANGLING", f"{path}.questionIds", f"unknown question: {question_id}")
        for question_id in _as_list(card.get("recommendedQuestionIds")):
            if question_id not in questions:
                report.add("QUESTION_DANGLING", f"{path}.recommendedQuestionIds", f"unknown question: {question_id}")
        for relation_id in _as_list(card.get("relationIds")) + _as_list(card.get("outgoingRelationIds")):
            if relation_id not in relations:
                report.add("RELATION_DANGLING", f"{path}.relationIds", f"unknown relation: {relation_id}")

    total_cards = len(cards)
    report.metrics["atomic_card_rate"] = round(atomic_cards / total_cards, 4) if total_cards else 0
    report.metrics["card_size_violation_rate"] = round(size_violations / total_cards, 4) if total_cards else 0


def _validate_sources(
    sources: dict[str, dict[str, Any]],
    questions: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> None:
    for source_id, source in sources.items():
        path = f"sources[{source_id}]"
        entity_type = source.get("entityType")
        if entity_type not in ENTITY_TYPES:
            report.add("SOURCE_UNCLASSIFIED", f"{path}.entityType", f"unknown entity type: {entity_type}")
        elif entity_type == "unclassified":
            report.add("SOURCE_UNCLASSIFIED", f"{path}.entityType", "source must be classified before readiness can pass")
        if not _non_empty_text(source.get("title")):
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.title", "source title is required")
        if not isinstance(source.get("provenance"), dict):
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.provenance", "source provenance is required")
        math_objects = _as_list(source.get("mathObjects"))
        math_object_ids: set[str] = set()
        for index, math_object in enumerate(math_objects):
            math_path = f"{path}.mathObjects[{index}]"
            if not isinstance(math_object, dict) or not _non_empty_text(math_object.get("id")):
                report.add("MATH_OBJECT_ID_MISSING", math_path, "math object id is required")
                continue
            math_id = math_object["id"]
            if math_id in math_object_ids:
                report.add("MATH_OBJECT_ID_DUPLICATE", f"{math_path}.id", f"duplicate math object: {math_id}")
            math_object_ids.add(math_id)
            if math_object.get("status") in {"UNREADABLE", "CONFLICTING"}:
                report.add("MATH_UNREADABLE", math_path, f"math object status: {math_object.get('status')}")
            elif math_object.get("status") == "LOST":
                report.add("MATH_CONTENT_LOSS", math_path, "source math object is marked LOST")

        if entity_type == "question_group":
            expected = _as_list(source.get("expectedQuestions"))
            linked = _as_list(source.get("questionIds"))
            if len(expected) > 1 or len(linked) > 1:
                report.add("QUESTION_GROUP_NOT_SPLIT", path, "question group must be split into one record per question")

        expected = _as_list(source.get("expectedQuestions"))
        if expected and entity_type == "question":
            actual = [question for question in questions.values() if source_id in _question_source_ids(question)]
            expected_keys = {key for item in expected if (key := _expected_question_key(item)) is not None}
            actual_keys = {_actual_question_identity(question) for question in actual}
            if expected_keys and expected_keys != actual_keys:
                report.add(
                    "QUESTION_IDENTITY_MISMATCH",
                    f"{path}.expectedQuestions",
                    f"expected {sorted(expected_keys)} but found {sorted(actual_keys)}",
                )


def _validate_relations(
    relations: dict[str, dict[str, Any]],
    modules: dict[str, dict[str, Any]],
    cards: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> None:
    entity_ids = set(modules) | set(cards)
    typed = 0
    reasons = 0
    for relation_id, relation in relations.items():
        path = f"relations[{relation_id}]"
        relation_type = relation.get("type")
        if not _non_empty_text(relation_type):
            report.add("RELATION_MISSING_TYPE", f"{path}.type", "typed relation type is required")
        elif relation_type not in RELATION_TYPES:
            report.add("RELATION_MISSING_TYPE", f"{path}.type", f"unknown relation type: {relation_type}")
        else:
            typed += 1
        from_id = relation.get("from")
        to_id = relation.get("to")
        if from_id not in entity_ids or to_id not in entity_ids or from_id == to_id:
            report.add("INVALID_RELATION_DIRECTION", path, "relation must have distinct existing from/to ids")
        if not _relation_reason_is_valid(relation.get("why")):
            report.add("RELATION_MISSING_REASON", f"{path}.why", "relation needs a specific mathematical reason")
        else:
            reasons += 1
        if relation.get("direction") in {"undirected", "bidirectional", "↔"}:
            report.add("INVALID_RELATION_DIRECTION", f"{path}.direction", "relations must be directed")

    total = len(relations)
    report.metrics["typed_relation_rate"] = round(typed / total, 4) if total else 0
    report.metrics["relation_reason_coverage"] = round(reasons / total, 4) if total else 0


def _validate_card_relation_ownership(
    cards: dict[str, dict[str, Any]],
    relations: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> None:
    for card_id, card in cards.items():
        if card.get("type") != "bridge":
            continue
        outgoing_ids = set(_as_list(card.get("outgoingRelationIds")))
        outgoing = [relation for relation in relations.values() if relation.get("from") == card_id]
        if not outgoing:
            report.add("EMPTY_BRIDGE", f"cards[{card_id}]", "bridge has no outgoing relation from its own id")
        declared = {relation.get("id") for relation in outgoing}
        if not outgoing_ids & declared:
            report.add("EMPTY_BRIDGE", f"cards[{card_id}].outgoingRelationIds", "declared bridge edges are not outgoing")


def _validate_questions(
    questions: dict[str, dict[str, Any]],
    cards: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> None:
    seen_fingerprints: dict[str, str] = {}
    valid_primary = 0
    duplicate_count = 0
    semantic_valid = 0
    math_valid = 0
    metadata_leakage = 0
    incomplete_count = 0
    for question_id, question in questions.items():
        path = f"questions[{question_id}]"
        question_type = question.get("type")
        if question_type not in QUESTION_TYPES:
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.type", f"unknown question type: {question_type}")
        source_ids = _question_source_ids(question)
        if not source_ids:
            report.add("QUESTION_IDENTITY_MISMATCH", f"{path}.sourceId", "question needs a sourceId")
        source_records = [sources[source_id] for source_id in source_ids if source_id in sources]
        primary_source = sources.get(question.get("sourceId"))
        if primary_source is not None and primary_source.get("entityType") != "question":
            if primary_source.get("entityType") in METADATA_ENTITY_TYPES:
                metadata_leakage += 1
                report.add("META_AS_QUESTION", path, f"primary source is metadata: {primary_source.get('id')}")
                report.add("SOURCE_METADATA_IN_QUESTION_BANK", path, f"primary source is {primary_source.get('entityType')}")
            else:
                report.add(
                    "QUESTION_IDENTITY_MISMATCH",
                    f"{path}.sourceId",
                    f"primary source must be entityType=question, got {primary_source.get('entityType')}",
                )
        for source in source_records:
            if source.get("entityType") in METADATA_ENTITY_TYPES:
                metadata_leakage += 1
                report.add("META_AS_QUESTION", path, f"question references metadata source: {source.get('id')}")
                report.add("SOURCE_METADATA_IN_QUESTION_BANK", path, f"question source is {source.get('entityType')}")
            if source.get("entityType") == "question_group":
                report.add("QUESTION_GROUP_NOT_SPLIT", path, "question still points at an unsplit question group")

        stem = question.get("stem")
        if not _meaningful(stem):
            incomplete_count += 1
            report.add("QUESTION_INCOMPLETE", f"{path}.stem", "question stem is missing")
        math_ids = _collect_math_object_ids(stem)
        math_ids.update(_collect_math_object_ids(question.get("options")))
        math_ids.update(_collect_math_object_ids(question.get("figures")))
        math_ids.update(_collect_math_object_ids(question.get("subparts")))
        math_content_lost = False
        for source in source_records:
            source_math_ids = {
                math_object.get("id")
                for math_object in _as_list(source.get("mathObjects"))
                if isinstance(math_object, dict) and _non_empty_text(math_object.get("id"))
            }
            for math_object in _as_list(source.get("mathObjects")):
                if not isinstance(math_object, dict):
                    continue
                status = math_object.get("status")
                if status in {"UNREADABLE", "CONFLICTING"}:
                    math_content_lost = True
                    report.add("MATH_UNREADABLE", f"{path}.sourceId", f"source math object {math_object.get('id')} is not readable")
                if status == "LOST":
                    math_content_lost = True
                    report.add("MATH_CONTENT_LOSS", f"{path}.sourceId", f"source math object {math_object.get('id')} is lost")
            expected_math_ids = set(_as_list(source.get("expectedMathObjectIds")))
            if expected_math_ids - math_ids:
                math_content_lost = True
                report.add(
                    "MATH_CONTENT_LOSS",
                    f"{path}.stem",
                    f"expected math objects missing from question: {sorted(expected_math_ids - math_ids)}",
                )
            math_ids.update(source_math_ids & set(_as_list(question.get("referencedMathObjectIds"))))

        question_status = question.get("questionStatus")
        if question_status not in STATUS_VALUES:
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.questionStatus", "questionStatus is missing or invalid")
        elif question_status != "COMPLETE":
            incomplete_count += 1
            report.add("QUESTION_INCOMPLETE", f"{path}.questionStatus", f"question status: {question_status}")

        source_status = question.get("sourceStatus")
        if source_status not in STATUS_VALUES:
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.sourceStatus", "sourceStatus is missing or invalid")
        elif source_status != "COMPLETE":
            report.add("SOURCE_INCOMPLETE", f"{path}.sourceStatus", f"source status: {source_status}")

        if question_type in {"multiple_choice", "single_choice", "multiple_select"}:
            options = question.get("options")
            option_values = list(options.values()) if isinstance(options, dict) else options if isinstance(options, list) else []
            if len(option_values) < 2:
                report.add("QUESTION_INCOMPLETE", f"{path}.options", "choice question needs at least two options")
            for index, option in enumerate(option_values):
                if not _option_has_content(option):
                    report.add("EMPTY_OPTION", f"{path}.options[{index}]", "option content is empty")

        solution = question.get("solution")
        solution_status = question.get("solutionStatus")
        if solution_status not in STATUS_VALUES:
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.solutionStatus", "solutionStatus is missing or invalid")
        if not isinstance(solution, dict) or not _meaningful(solution.get("text")):
            report.add("SOLUTION_INCOMPLETE", f"{path}.solution", "solution text is missing")
        else:
            solution_text = str(solution.get("text"))
            if solution_status == "COMPLETE" and any(pattern.search(solution_text) for pattern in INCOMPLETE_SOLUTION_PATTERNS):
                report.add("SOLUTION_INCOMPLETE", f"{path}.solution.text", "solution contains an incomplete placeholder")
            referenced_math_ids = set(_as_list(solution.get("referencesMathObjectIds")))
            if referenced_math_ids - math_ids:
                report.add(
                    "QUESTION_SOLUTION_MISMATCH",
                    f"{path}.solution.referencesMathObjectIds",
                    f"solution references math objects not present in the question: {sorted(referenced_math_ids - math_ids)}",
                )
        if solution_status not in {"COMPLETE", "DERIVED_COMPLETE", "OFFICIAL_COMPLETE", "HISTORICAL_COMPLETE"}:
            report.add("SOLUTION_INCOMPLETE", f"{path}.solutionStatus", f"solution status: {solution_status}")

        solution_evidence = _as_list(question.get("solutionEvidence"))
        solution_evidence_kinds: set[str] = set()
        for index, evidence in enumerate(solution_evidence):
            evidence_path = f"{path}.solutionEvidence[{index}]"
            if not isinstance(evidence, dict) or evidence.get("kind") not in SOLUTION_EVIDENCE_KINDS:
                report.add("ANSWER_PROVENANCE_CONFLICT", evidence_path, "solution evidence kind is invalid")
                continue
            solution_evidence_kinds.add(evidence["kind"])
            if not _non_empty_text(evidence.get("sourceId")) or evidence["sourceId"] not in sources:
                report.add("ANSWER_PROVENANCE_CONFLICT", evidence_path, "solution evidence source does not exist")
        for field_name, evidence_kind in (
            ("officialSolution", "official_solution"),
            ("historicalSolution", "historical_solution"),
            ("derivedSolution", "derived_solution"),
        ):
            value = question.get(field_name)
            if value is None:
                continue
            solution_text = value.get("text") if isinstance(value, dict) else value
            if not _meaningful(solution_text):
                report.add("SOLUTION_INCOMPLETE", f"{path}.{field_name}", "solution text is missing")
            if evidence_kind not in solution_evidence_kinds:
                report.add("ANSWER_PROVENANCE_CONFLICT", f"{path}.{field_name}", f"{field_name} lacks matching solution evidence")
            if field_name == "derivedSolution" and not _non_empty_text(value.get("origin") if isinstance(value, dict) else None):
                report.add("DERIVED_PROVENANCE_MISSING", f"{path}.{field_name}", "derived solution needs an origin label")

        primary_card_id = question.get("primaryCardId")
        declared_primary = question.get("primaryCardIds")
        if isinstance(declared_primary, list) and len(declared_primary) != 1:
            report.add("QUESTION_MULTIPLE_PRIMARY_CARDS", f"{path}.primaryCardIds", "exactly one primary card is required")
        if not _non_empty_text(primary_card_id):
            report.add("QUESTION_WITHOUT_PRIMARY_CARD", f"{path}.primaryCardId", "primary card is required")
        elif primary_card_id not in cards:
            report.add("QUESTION_WITHOUT_PRIMARY_CARD", f"{path}.primaryCardId", f"unknown primary card: {primary_card_id}")
        else:
            valid_primary += 1
        secondary = _as_list(question.get("secondaryCardIds"))
        if len(secondary) != len(set(secondary)):
            report.add("QUESTION_CARD_MISMATCH", f"{path}.secondaryCardIds", "secondary card ids must be unique")
        if primary_card_id in secondary:
            report.add("QUESTION_MULTIPLE_PRIMARY_CARDS", f"{path}.secondaryCardIds", "primary card cannot also be secondary")
        for card_id in secondary:
            if card_id not in cards:
                report.add("QUESTION_CARD_MISMATCH", f"{path}.secondaryCardIds", f"unknown secondary card: {card_id}")

        mapping = question.get("mappingEvidence")
        mapping_operations = set(mapping.get("coreOperations", [])) if isinstance(mapping, dict) else set()
        if not isinstance(mapping, dict) or not _non_empty_text(mapping.get("whyPrimary")) or not mapping_operations:
            report.add("QUESTION_CARD_MISMATCH", f"{path}.mappingEvidence", "mapping needs core operations and whyPrimary")
        if primary_card_id in cards:
            card = cards[primary_card_id]
            card_operations = set(_as_list(card.get("operationTags")))
            if mapping_operations and card_operations.isdisjoint(mapping_operations):
                report.add("QUESTION_CARD_MISMATCH", path, "primary card operationTags do not support the mapped operation")
            if question_id not in _as_list(card.get("questionIds")):
                report.add("QUESTION_CARD_MISMATCH", path, "primary card does not reference this question id")

        answer_status = question.get("answerStatus")
        if answer_status not in STATUS_VALUES:
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"{path}.answerStatus", "answerStatus is missing or invalid")
        answer_evidence = _as_list(question.get("answerEvidence"))
        evidence_kinds: set[str] = set()
        for index, evidence in enumerate(answer_evidence):
            evidence_path = f"{path}.answerEvidence[{index}]"
            if not isinstance(evidence, dict) or evidence.get("kind") not in ANSWER_EVIDENCE_KINDS:
                report.add("ANSWER_PROVENANCE_CONFLICT", evidence_path, "answer evidence kind is invalid")
                continue
            evidence_kinds.add(evidence["kind"])
            if not _meaningful(evidence.get("value")) or not _non_empty_text(evidence.get("sourceId")):
                report.add("ANSWER_PROVENANCE_CONFLICT", evidence_path, "answer evidence needs value and sourceId")
            elif evidence["sourceId"] not in sources:
                report.add("ANSWER_PROVENANCE_CONFLICT", evidence_path, "answer evidence source does not exist")

        official = question.get("officialAnswer")
        historical = question.get("historicalAnswer")
        derived = question.get("derivedAnswer")
        if official is not None and "official_answer" not in evidence_kinds:
            report.add("ANSWER_PROVENANCE_CONFLICT", f"{path}.officialAnswer", "official answer lacks official evidence")
        if historical is not None and "historical_answer" not in evidence_kinds:
            report.add("ANSWER_PROVENANCE_CONFLICT", f"{path}.historicalAnswer", "historical answer lacks historical evidence")
        if derived is not None and "derived_answer" not in evidence_kinds:
            report.add("ANSWER_PROVENANCE_CONFLICT", f"{path}.derivedAnswer", "derived answer lacks derivation evidence")
        if official is not None and derived is not None and _normalize(official) != _normalize(derived):
            report.add("ANSWER_PROVENANCE_CONFLICT", path, "official and derived answers disagree")
        if derived is not None and (question_status != "COMPLETE" or math_content_lost):
            report.add("DERIVED_ANSWER_FORBIDDEN", f"{path}.derivedAnswer", "cannot derive an answer from an incomplete question")
        if question.get("derivedSolution") is not None and (question_status != "COMPLETE" or math_content_lost):
            report.add("DERIVED_SOLUTION_FORBIDDEN", f"{path}.derivedSolution", "cannot derive a solution from an incomplete question")
        if answer_status == "ANSWER_UNVERIFIED":
            report.add("ANSWER_UNVERIFIED", f"{path}.answerStatus", "answer is explicitly unverified")
        if answer_status == "ANSWER_MISSING":
            report.add("ANSWER_MISSING", f"{path}.answerStatus", "answer is not available for exam use")
        if answer_status == "ANSWER_VERIFIED" and official is None and derived is None:
            report.add("QUESTION_ANSWER_MISMATCH", f"{path}.answerStatus", "verified answer has no official or derived value")
        if answer_status == "DERIVED_VERIFIED" and derived is None:
            report.add("QUESTION_ANSWER_MISMATCH", f"{path}.answerStatus", "derived verified status has no derived answer")

        semantic = question.get("semanticProfile")
        if not isinstance(semantic, dict):
            report.add("QUESTION_SOLUTION_MISMATCH", f"{path}.semanticProfile", "semantic profile is required")
        else:
            stem_concepts = set(_as_list(semantic.get("stemConcepts")))
            solution_concepts = set(_as_list(semantic.get("solutionConcepts")))
            allowed = set(_as_list(semantic.get("allowedDerivedConcepts")))
            unexpected = solution_concepts - stem_concepts - allowed
            if unexpected:
                report.add(
                    "QUESTION_SOLUTION_MISMATCH",
                    f"{path}.semanticProfile.solutionConcepts",
                    f"solution concepts are not supported by the stem: {sorted(unexpected)}",
                )
            else:
                semantic_valid += 1

        stem_fingerprint = _fingerprint(stem)
        duplicate_key = f"{question_type}|{question.get('originalNumber')}|{stem_fingerprint}"
        if _meaningful(stem):
            if duplicate_key in seen_fingerprints:
                duplicate_count += 1
                report.add(
                    "QUESTION_DUPLICATED",
                    path,
                    f"same question fingerprint as {seen_fingerprints[duplicate_key]}",
                )
            else:
                seen_fingerprints[duplicate_key] = question_id

        if not any(issue.path == path or issue.path.startswith(f"{path}.") for issue in report.issues if issue.code in {"MATH_UNREADABLE", "MATH_CONTENT_LOSS"}):
            math_valid += 1

    total_questions = len(questions)
    report.metrics["question_primary_mapping_rate"] = round(valid_primary / total_questions, 4) if total_questions else 0
    report.metrics["question_duplicate_rate"] = round(duplicate_count / total_questions, 4) if total_questions else 0
    report.metrics["metadata_leakage_rate"] = round(metadata_leakage / total_questions, 4) if total_questions else 0
    report.metrics["question_semantic_validation_rate"] = round(semantic_valid / total_questions, 4) if total_questions else 0
    report.metrics["math_integrity_pass_rate"] = round(math_valid / total_questions, 4) if total_questions else 0
    report.metrics["question_incomplete_count"] = incomplete_count


def _validate_progress(record: dict[str, Any], cards: dict[str, dict[str, Any]], questions: dict[str, dict[str, Any]], report: ValidationReport) -> None:
    progress = record.get("progress")
    if not isinstance(progress, dict):
        report.add("DOMAIN_TEMPLATE_MISMATCH", "progress", "progress object is required")
        return
    for key, allowed_ids in (("knowledgeMastery", set(cards)), ("questionMastery", set(questions))):
        mastery = progress.get(key)
        if not isinstance(mastery, dict):
            report.add("DOMAIN_TEMPLATE_MISMATCH", f"progress.{key}", "mastery object is required")
            continue
        for bucket in ("knownCardIds", "reviewCardIds", "unknownCardIds") if key == "knowledgeMastery" else ("solvedQuestionIds", "reviewQuestionIds", "unseenQuestionIds"):
            for item_id in _as_list(mastery.get(bucket)):
                if item_id not in allowed_ids:
                    report.add("DOMAIN_TEMPLATE_MISMATCH", f"progress.{key}.{bucket}", f"unknown id: {item_id}")


def validate_record(record: Any) -> ValidationReport:
    report = ValidationReport()
    if not isinstance(record, dict):
        report.add("SCHEMA_ROOT_NOT_OBJECT", "", "structured math record must be an object")
        return report
    _validate_top_level(record, report)
    modules_records = record.get("modules", []) if isinstance(record.get("modules", []), list) else []
    cards_records = record.get("cards", []) if isinstance(record.get("cards", []), list) else []
    questions_records = record.get("questions", []) if isinstance(record.get("questions", []), list) else []
    relations_records = record.get("relations", []) if isinstance(record.get("relations", []), list) else []
    sources_records = record.get("sources", []) if isinstance(record.get("sources", []), list) else []
    modules = _index_by_id(modules_records, "modules", report)
    cards = _index_by_id(cards_records, "cards", report)
    questions = _index_by_id(questions_records, "questions", report, "QUESTION_ID_MISSING")
    relations = _index_by_id(relations_records, "relations", report)
    sources = _index_by_id(sources_records, "sources", report)
    _validate_modules(modules, cards, sources, report)
    _validate_sources(sources, questions, report)
    _validate_relations(relations, modules, cards, report)
    _validate_cards(cards, modules, questions, sources, relations, report)
    _validate_card_relation_ownership(cards, relations, report)
    _validate_questions(questions, cards, sources, report)
    _validate_progress(record, cards, questions, report)
    subject = record.get("subject")
    if isinstance(subject, dict):
        expected_status = "可用于考试" if not report.errors else "学习未完成"
        declared_status = subject.get("learningStatus")
        if declared_status is not None and declared_status != expected_status:
            report.add(
                "LEARNING_STATUS_MISMATCH",
                "subject.learningStatus",
                f"declared {declared_status!r}, but validator computed {expected_status!r}",
            )
    report.metrics["relation_count"] = len(relations)
    report.metrics["card_count"] = len(cards)
    report.metrics["question_count"] = len(questions)
    report.metrics["source_count"] = len(sources)
    report.metrics["learning_status"] = "可用于考试" if report.passed else "学习未完成"
    return report


def _json_default(value: Any) -> Any:
    if isinstance(value, Issue):
        return asdict(value)
    raise TypeError(f"unsupported value: {type(value)!r}")


def render_report(report: ValidationReport, as_json: bool = False) -> str:
    payload = {
        "passed": report.passed,
        "examReadiness": "PASS" if report.passed else "FAIL",
        "learningStatus": report.metrics.get("learning_status"),
        "issues": [asdict(issue) for issue in report.issues],
        "metrics": report.metrics,
    }
    if as_json:
        return json.dumps(payload, ensure_ascii=False, indent=2)
    lines = [
        f"EXAM_READINESS: {payload['examReadiness']}",
        f"LEARNING_STATUS: {payload['learningStatus']}",
        "ISSUES:",
    ]
    if report.issues:
        lines.extend(f"- [{issue.code}] {issue.path}: {issue.message}" for issue in report.issues)
    else:
        lines.append("- none")
    lines.append("METRICS:")
    lines.extend(f"- {key}: {value}" for key, value in sorted(report.metrics.items()))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate structured study-math JSON records.")
    parser.add_argument("record", type=Path, help="Structured math record JSON file")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    report = validate_record(record)
    print(render_report(report, as_json=args.as_json))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
