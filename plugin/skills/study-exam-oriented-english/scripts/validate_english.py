"""Validate an evidence-backed exam-oriented English domain record."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "study-exam-oriented-english.record.v1"
CARD_TYPES = {
    "expression-function",
    "grammar-pattern",
    "writing-structure",
    "translation-pattern",
    "error-pattern",
    "vocabulary-in-context",
    "sentence-bridge",
}
LEVELS = {"basic", "standard", "advanced"}
LOGIC_RELATIONS = {"negation", "causal", "comparison", "condition", "concession", "contrast", "scope", "uncertainty"}
QUALITY_FIELDS = ("contentCompletion", "clarity", "coherence", "grammarAccuracy", "lexicalAccuracy", "genreFit", "naturalness")


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list(value: Any) -> bool:
    return isinstance(value, list)


def _refs(value: Any, path: str) -> list[str]:
    if not isinstance(value, list) or not value:
        return [f"{path} must be a non-empty list"]
    errors: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict) or not _text(item.get("sourceId")) or not _text(item.get("locator")):
            errors.append(f"{path}[{index}] must contain sourceId and locator")
    return errors


def _quality(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors: list[str] = []
    for field in QUALITY_FIELDS:
        score = value.get(field)
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 1:
            errors.append(f"{path}.{field} must be between 0 and 1")
    if "advancedWordCount" in value or "complexityScore" in value:
        errors.append(f"{path} must not optimize by word count or complexity score")
    return errors


def _writing(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors: list[str] = []
    examples = value.get("examples")
    if not isinstance(examples, list) or not examples:
        return [f"{path}.examples must be non-empty"]
    ids: set[str] = set()
    for index, item in enumerate(examples):
        item_path = f"{path}.examples[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object")
            continue
        for field in ("id", "taskType", "prompt", "recommendedText"):
            if not _text(item.get(field)):
                errors.append(f"{item_path}.{field} must be non-empty")
        if item.get("id") in ids:
            errors.append(f"{item_path}.id is duplicated")
        if _text(item.get("id")):
            ids.add(item["id"])
        if item.get("level") not in LEVELS:
            errors.append(f"{item_path}.level is invalid")
        intent = item.get("intentUnits")
        preserved = item.get("meaningUnitsPreserved")
        if not isinstance(intent, list) or not intent or any(not _text(unit) for unit in intent):
            errors.append(f"{item_path}.intentUnits must contain text units")
        if not isinstance(preserved, list) or not set(intent or []).issubset(set(preserved)):
            errors.append(f"{item_path}.meaningUnitsPreserved must cover every intent unit")
        errors.extend(_refs(item.get("sourceRefs"), f"{item_path}.sourceRefs"))
        errors.extend(_quality(item.get("quality"), f"{item_path}.quality"))
        if item.get("unchanged") is True and item.get("originalText") != item.get("recommendedText"):
            errors.append(f"{item_path} marked unchanged but text differs")
        if item.get("unchanged") is True and not _text(item.get("preserveReason")):
            errors.append(f"{item_path}.preserveReason is required for unchanged text")
    return errors


def _translation(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    examples = value.get("examples")
    if not isinstance(examples, list) or not examples:
        return [f"{path}.examples must be non-empty"]
    errors: list[str] = []
    ids: set[str] = set()
    for index, item in enumerate(examples):
        item_path = f"{path}.examples[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object")
            continue
        for field in ("id", "sourceText", "mainClause", "recommendedTranslation"):
            if not _text(item.get(field)):
                errors.append(f"{item_path}.{field} must be non-empty")
        if item.get("id") in ids:
            errors.append(f"{item_path}.id is duplicated")
        if _text(item.get("id")):
            ids.add(item["id"])
        relations = item.get("logicRelations")
        preserved = item.get("preservedLogicRelations")
        if not isinstance(relations, list) or any(relation not in LOGIC_RELATIONS for relation in relations):
            errors.append(f"{item_path}.logicRelations contains an invalid relation")
        if not isinstance(preserved, list) or not set(relations or []).issubset(set(preserved)):
            errors.append(f"{item_path}.preservedLogicRelations must cover source logic")
        units = item.get("meaningUnits")
        preserved_units = item.get("preservedMeaningUnits")
        if not isinstance(units, list) or not units or any(not _text(unit) for unit in units):
            errors.append(f"{item_path}.meaningUnits must contain text units")
        if not isinstance(preserved_units, list) or not set(units or []).issubset(set(preserved_units)):
            errors.append(f"{item_path}.preservedMeaningUnits must cover source meaning")
        terms = item.get("keyTerms")
        if not isinstance(terms, list) or not terms:
            errors.append(f"{item_path}.keyTerms must be non-empty")
        else:
            for term_index, term in enumerate(terms):
                if not isinstance(term, dict) or not _text(term.get("term")) or not _text(term.get("contextMeaning")) or term.get("preserved") is not True:
                    errors.append(f"{item_path}.keyTerms[{term_index}] must preserve a contextual term")
        errors.extend(_refs(item.get("sourceRefs"), f"{item_path}.sourceRefs"))
    return errors


def _review(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors: list[str] = []
    revisions = value.get("writingRevisions")
    diagnostics = value.get("translationDiagnostics")
    if not isinstance(revisions, list) or not revisions:
        errors.append(f"{path}.writingRevisions must be non-empty")
    else:
        for index, item in enumerate(revisions):
            item_path = f"{path}.writingRevisions[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{item_path} must be an object")
                continue
            for field in ("sentenceId", "original", "recommended", "reason"):
                if not _text(item.get(field)):
                    errors.append(f"{item_path}.{field} must be non-empty")
            if not isinstance(item.get("issueCodes"), list) or not item["issueCodes"]:
                errors.append(f"{item_path}.issueCodes must be non-empty")
            errors.extend(_refs(item.get("evidenceRefs"), f"{item_path}.evidenceRefs"))
            if not isinstance(item.get("preserveIfCorrect"), bool):
                errors.append(f"{item_path}.preserveIfCorrect must be boolean")
    if not isinstance(diagnostics, list) or not diagnostics:
        errors.append(f"{path}.translationDiagnostics must be non-empty")
    else:
        for index, item in enumerate(diagnostics):
            item_path = f"{path}.translationDiagnostics[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{item_path} must be an object")
                continue
            for field in ("sentenceId", "sourceFragment", "userTranslation", "diagnosis", "recommendation"):
                if not _text(item.get(field)):
                    errors.append(f"{item_path}.{field} must be non-empty")
            if not isinstance(item.get("errorCodes"), list) or not item["errorCodes"]:
                errors.append(f"{item_path}.errorCodes must be non-empty")
            if item.get("status") not in {"confirmed", "hypothesis", "unknown", "blocked"}:
                errors.append(f"{item_path}.status is invalid")
            errors.extend(_refs(item.get("evidenceRefs"), f"{item_path}.evidenceRefs"))
    return errors


def _integrations(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors: list[str] = []
    for name in ("practice", "review", "optimize", "healExam"):
        item = value.get(name)
        if not isinstance(item, dict) or item.get("enabled") is not True:
            errors.append(f"{path}.{name}.enabled must be true")
    return errors


def validate_record(record: Any) -> list[str]:
    if not isinstance(record, dict):
        return ["record must be an object"]
    errors: list[str] = []
    if record.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if record.get("domain") != "study-exam-oriented-english":
        errors.append("domain must be study-exam-oriented-english")
    if not _text(record.get("subjectId")):
        errors.append("subjectId must be non-empty")
    cards = record.get("cards")
    if not isinstance(cards, list) or not cards:
        errors.append("cards must be non-empty")
        cards = []
    card_ids: set[str] = set()
    for index, card in enumerate(cards):
        path = f"cards[{index}]"
        if not isinstance(card, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("id", "title", "coreMeaning", "recallPrompt"):
            if not _text(card.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if card.get("id") in card_ids:
            errors.append(f"{path}.id is duplicated")
        if _text(card.get("id")):
            card_ids.add(card["id"])
        if card.get("type") not in CARD_TYPES:
            errors.append(f"{path}.type is invalid")
        if card.get("difficulty") not in LEVELS:
            errors.append(f"{path}.difficulty is invalid")
        errors.extend(_refs(card.get("sourceRefs"), f"{path}.sourceRefs"))
    errors.extend(_writing(record.get("writing"), "writing"))
    errors.extend(_translation(record.get("translation"), "translation"))
    errors.extend(_review(record.get("review"), "review"))
    errors.extend(_integrations(record.get("integrations"), "integrations"))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an exam-oriented English domain record.")
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_record(record)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated English domain record {record['subjectId']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
