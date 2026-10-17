"""Validate local learner-model records without inferring personality traits."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STAGES = {"PERCEPTION", "INTERPRETATION", "RETRIEVAL", "METHOD_SELECTION", "CONDITION_CHECK", "SETUP", "EXECUTION", "INTEGRATION", "VERIFICATION", "EXPRESSION"}
EVENTS = {"incorrect", "correct", "hinted_correct", "independent_correct", "recall", "user_correction", "explanation_feedback"}
ERROR_STATUSES = {"active", "improving", "dormant", "resolved"}
FORBIDDEN_INFERENCE_KEYS = {"personality", "learningStyle", "intelligence", "memoryAbility", "visualLearner", "logicalAbility"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _int(value: Any, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _number(value: Any, low: float = 0, high: float = 1) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high


def _forbidden(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return []
    return [key for key in data if key in FORBIDDEN_INFERENCE_KEYS]


def validate_observation(observation: Any) -> list[str]:
    if not isinstance(observation, dict):
        return ["observation must be an object"]
    errors: list[str] = []
    for field in ("id", "subjectId", "timestamp", "entityType", "entityId", "taskStage", "source"):
        if not _text(observation.get(field)):
            errors.append(f"{field} must be non-empty")
    if observation.get("event") not in EVENTS:
        errors.append("event is invalid")
    if observation.get("taskStage") not in STAGES:
        errors.append("taskStage is invalid")
    if "hintCount" in observation and not _int(observation["hintCount"]):
        errors.append("hintCount must be a non-negative integer")
    errors.extend(f"forbidden inference field: {key}" for key in _forbidden(observation))
    return errors


def validate_error_model(model: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(model, dict) or not _text(model.get("subjectId")) or not _int(model.get("learningEpoch"), 1):
        return ["subjectId and learningEpoch are required"]
    patterns = model.get("patterns")
    if not isinstance(patterns, list):
        return ["patterns must be a list"]
    for index, pattern in enumerate(patterns):
        path = f"patterns[{index}]"
        if not isinstance(pattern, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in ("code", "stage", "firstSeen", "lastSeen"):
            if not _text(pattern.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        if pattern.get("stage") not in STAGES:
            errors.append(f"{path}.stage is invalid")
        if not _int(pattern.get("count"), 1) or not _int(pattern.get("recentCount")):
            errors.append(f"{path}.count and recentCount must be valid integers")
        elif pattern["recentCount"] > pattern["count"]:
            errors.append(f"{path}.recentCount cannot exceed count")
        if not _number(pattern.get("confidence")):
            errors.append(f"{path}.confidence must be between 0 and 1")
        elif pattern.get("count") == 1 and pattern["confidence"] >= 0.9:
            errors.append(f"{path}.confidence is too high for one observation")
        if pattern.get("status") not in ERROR_STATUSES:
            errors.append(f"{path}.status is invalid")
        if not isinstance(pattern.get("evidenceIds"), list) or not pattern["evidenceIds"]:
            errors.append(f"{path}.evidenceIds must not be empty")
        errors.extend(f"{path}.{key} is forbidden" for key in _forbidden(pattern))
    return errors


def validate_explanation_model(model: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(model, dict) or not _text(model.get("scope")):
        return ["scope is required"]
    patterns = model.get("patterns")
    if not isinstance(patterns, list):
        return ["patterns must be a list"]
    for index, pattern in enumerate(patterns):
        path = f"patterns[{index}]"
        if not isinstance(pattern, dict):
            errors.append(f"{path} must be an object")
            continue
        if not isinstance(pattern.get("strategy"), list) or not pattern["strategy"]:
            errors.append(f"{path}.strategy must not be empty")
        if not _number(pattern.get("effectiveness")):
            errors.append(f"{path}.effectiveness must be between 0 and 1")
        if not _int(pattern.get("evidenceCount"), 1) or not _int(pattern.get("successfulTransfers")):
            errors.append(f"{path}.evidence counters are invalid")
        elif pattern["successfulTransfers"] > pattern["evidenceCount"]:
            errors.append(f"{path}.successfulTransfers cannot exceed evidenceCount")
        if not isinstance(pattern.get("evidenceIds"), list) or not pattern["evidenceIds"]:
            errors.append(f"{path}.evidenceIds must not be empty")
        if not _text(pattern.get("lastUpdated")):
            errors.append(f"{path}.lastUpdated must be non-empty")
        errors.extend(f"{path}.{key} is forbidden" for key in _forbidden(pattern))
    return errors


def validate_mastery(model: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(model, dict) or not _text(model.get("subjectId")) or not _int(model.get("learningEpoch"), 1):
        return ["subjectId and learningEpoch are required"]
    cards = model.get("cards")
    if not isinstance(cards, dict):
        return ["cards must be an object"]
    for card_id, mastery in cards.items():
        if not isinstance(mastery, dict):
            errors.append(f"cards.{card_id} must be an object")
            continue
        for field in ("recognize", "recall", "apply", "transfer"):
            if not _number(mastery.get(field)):
                errors.append(f"cards.{card_id}.{field} must be between 0 and 1")
        if not isinstance(mastery.get("evidenceIds"), list) or not mastery["evidenceIds"]:
            errors.append(f"cards.{card_id}.evidenceIds must not be empty")
    return errors


def validate_sort_state(state: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return ["sort state must be an object"]
    for field in ("subjectId", "generatedAt", "artifactVersion", "artifactHash"):
        if not _text(state.get(field)):
            errors.append(f"{field} must be non-empty")
    ranking = state.get("ranking")
    if not isinstance(ranking, list):
        return errors + ["ranking must be a list"]
    seen: set[str] = set()
    for index, item in enumerate(ranking):
        path = f"ranking[{index}]"
        if not isinstance(item, dict) or not _text(item.get("cardId")):
            errors.append(f"{path}.cardId must be non-empty")
            continue
        if item["cardId"] in seen:
            errors.append(f"{path}.cardId is duplicated")
        seen.add(item["cardId"])
        if not isinstance(item.get("priorityScore"), (int, float)):
            errors.append(f"{path}.priorityScore must be numeric")
        if not isinstance(item.get("reasons"), list) or not item["reasons"]:
            errors.append(f"{path}.reasons must not be empty")
        if not isinstance(item.get("evidenceIds"), list) or not item["evidenceIds"]:
            errors.append(f"{path}.evidenceIds must not be empty")
    return errors


def validate_strategy_state(state: Any) -> list[str]:
    if not isinstance(state, dict):
        return ["strategy state must be an object"]
    errors: list[str] = []
    for field in ("subjectId", "scope", "updatedAt"):
        if not _text(state.get(field)):
            errors.append(f"{field} must be non-empty")
    if not _int(state.get("learningEpoch"), 1):
        errors.append("learningEpoch must be a positive integer")
    for field in ("strategy", "reasonCodes", "evidenceIds"):
        if not isinstance(state.get(field), list) or not state[field]:
            errors.append(f"{field} must not be empty")
    errors.extend(f"forbidden inference field: {key}" for key in _forbidden(state))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate local learner-model records.")
    parser.add_argument("kind", choices=["observation", "error-model", "explanation-model", "mastery", "strategy-state", "sort-state"])
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    data = json.loads(args.path.read_text(encoding="utf-8"))
    validators = {
        "observation": validate_observation,
        "error-model": validate_error_model,
        "explanation-model": validate_explanation_model,
        "mastery": validate_mastery,
        "strategy-state": validate_strategy_state,
        "sort-state": validate_sort_state,
    }
    errors = validators[args.kind](data)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated learner {args.kind}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
