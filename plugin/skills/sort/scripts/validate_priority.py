"""Validate the deterministic, evidence-backed review-priority projection."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


DIMENSIONS = (
    "exam_importance",
    "error_risk",
    "dependency_weight",
    "user_weakness",
    "recent_exam_errors",
    "coverage_gap",
    "confusion_density",
    "recall_difficulty",
    "question_frequency",
)
MODES = {"default", "exam", "weakness", "risk", "prerequisite", "tonight"}
REASON_CODES = {
    "high_exam_importance": "exam_importance",
    "high_error_risk": "error_risk",
    "high_dependency": "dependency_weight",
    "user_weakness": "user_weakness",
    "recent_exam_error": "recent_exam_errors",
    "coverage_gap": "coverage_gap",
    "often_confused": "confusion_density",
    "hard_to_recall": "recall_difficulty",
    "high_question_frequency": "question_frequency",
    "insufficient_signal": None,
}
STATUSES = {"ready", "partial", "insufficient-signal"}
ENTRY_STATUSES = {"ranked", "insufficient-signal"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _evidence(value: Any) -> bool:
    if _text(value):
        return True
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, dict) and any(_text(part) for part in item.values()) for item in value
    )


def _expected_score(dimensions: dict[str, Any], weights: dict[str, float]) -> tuple[float | None, float]:
    known = [name for name in DIMENSIONS if _number(dimensions.get(name))]
    if any(name not in weights for name in known):
        return None, 0.0
    known_weight = sum(weights[name] for name in known)
    if not known:
        return None, 0.0
    score = sum(weights[name] * float(dimensions[name]) for name in known) / known_weight
    return round(score, 2), known_weight


def _priority(entry: dict[str, Any], path: str, errors: list[str], weights: dict[str, float]) -> tuple[float | None, float]:
    priority = entry.get("priority")
    if not isinstance(priority, dict):
        errors.append(f"{path}.priority must be an object")
        return None, 0.0
    if priority.get("status") not in ENTRY_STATUSES:
        errors.append(f"{path}.priority.status is invalid")
    score = priority.get("score")
    if score is not None and (not _number(score) or not 0 <= score <= 100):
        errors.append(f"{path}.priority.score must be null or a number from 0 through 100")
    confidence = priority.get("confidence")
    if not _number(confidence) or not 0 <= confidence <= 1:
        errors.append(f"{path}.priority.confidence must be a number from 0 through 1")
    dimensions = priority.get("dimensions")
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
        errors.append(f"{path}.priority.dimensions must contain exactly the nine priority dimensions")
        dimensions = {name: None for name in DIMENSIONS}
    for name in DIMENSIONS:
        value = dimensions.get(name)
        if value is not None and (not _number(value) or not 0 <= value <= 100):
            errors.append(f"{path}.priority.dimensions.{name} must be null or a number from 0 through 100")
    reasons = priority.get("reasons")
    if not isinstance(reasons, list) or not reasons:
        errors.append(f"{path}.priority.reasons must be a non-empty list")
        reasons = []
    reason_codes: set[str] = set()
    for index, reason in enumerate(reasons):
        reason_path = f"{path}.priority.reasons[{index}]"
        if not isinstance(reason, dict):
            errors.append(f"{reason_path} must be an object")
            continue
        code = reason.get("code")
        if code not in REASON_CODES:
            errors.append(f"{reason_path}.code is invalid")
        else:
            reason_codes.add(code)
            dimension = REASON_CODES[code]
            if dimension is not None and dimensions.get(dimension) is None:
                errors.append(f"{reason_path}.code has no supporting dimension value")
        if not _text(reason.get("label")):
            errors.append(f"{reason_path}.label must be non-empty")
        if not _evidence(reason.get("evidence")):
            errors.append(f"{reason_path}.evidence must contain a location or evidence object")

    expected_score, known_weight = _expected_score(dimensions, weights)
    if score is None:
        if priority.get("status") != "insufficient-signal":
            errors.append(f"{path}.priority.status must be insufficient-signal when score is null")
        if confidence != 0:
            errors.append(f"{path}.priority.confidence must be 0 when score is null")
        if "insufficient_signal" not in reason_codes:
            errors.append(f"{path}.priority.reasons must include insufficient_signal when score is null")
    elif priority.get("status") != "ranked":
        errors.append(f"{path}.priority.status must be ranked when score is numeric")
    return expected_score, known_weight


def validate_result(result: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return ["result must be an object"]
    if result.get("schemaVersion") != "sort.priority.v1":
        errors.append("schemaVersion must be sort.priority.v1")
    if result.get("inputsReadOnly") is not True:
        errors.append("inputsReadOnly must be true")
    if result.get("mode") not in MODES:
        errors.append("mode is invalid")
    for field in (
        "subject",
        "artifact",
        "model",
        "inputs",
        "canonicalStructurePreserved",
        "selection",
        "queue",
        "reviewOrder",
        "reviewQueue",
        "summary",
        "status",
    ):
        if field not in result:
            errors.append(f"{field} is required")
    subject = result.get("subject")
    if not isinstance(subject, dict) or not _text(subject.get("id")) or not _text(subject.get("title")):
        errors.append("subject.id and subject.title are required")
    artifact = result.get("artifact")
    if not isinstance(artifact, dict) or not _text(artifact.get("version")) or not _text(artifact.get("generatedAt")):
        errors.append("artifact.version and artifact.generatedAt are required")
    if not isinstance(result.get("inputs"), dict):
        errors.append("inputs must be an object")
    if result.get("status") not in STATUSES:
        errors.append("status is invalid")

    model = result.get("model")
    weights: dict[str, float] = {}
    if not isinstance(model, dict):
        errors.append("model must be an object")
    else:
        if not _text(model.get("version")):
            errors.append("model.version must be non-empty")
        if model.get("dimensions") != list(DIMENSIONS):
            errors.append("model.dimensions must list the nine priority dimensions in order")
        raw_weights = model.get("weights")
        if not isinstance(raw_weights, dict) or set(raw_weights) != set(DIMENSIONS):
            errors.append("model.weights must contain exactly the nine priority dimensions")
        else:
            for name in DIMENSIONS:
                value = raw_weights[name]
                if not _number(value) or not 0 <= value <= 1:
                    errors.append(f"model.weights.{name} must be between 0 and 1")
                else:
                    weights[name] = float(value)
            if weights and abs(sum(weights.values()) - 1.0) > 0.0001:
                errors.append("model.weights must sum to 1.0")
        if model.get("missingSignalPolicy") != "exclude_and_flag":
            errors.append("model.missingSignalPolicy must be exclude_and_flag")

    preserved = result.get("canonicalStructurePreserved")
    required_false_flags = ("contentMutated", "relationsMutated", "sourceMutated", "chapterOrderMutated")
    if not isinstance(preserved, dict) or preserved.get("preserved") is not True:
        errors.append("canonicalStructurePreserved.preserved must be true")
    elif any(preserved.get(flag) is not False for flag in required_false_flags):
        errors.append("canonicalStructurePreserved must show no canonical mutations")

    selection = result.get("selection")
    if not isinstance(selection, dict) or not _text(selection.get("policy")):
        errors.append("selection.policy is required")
    elif selection.get("excludedCardIds") is not None and not isinstance(selection.get("excludedCardIds"), list):
        errors.append("selection.excludedCardIds must be a list")

    queue = result.get("queue")
    if not isinstance(queue, list):
        return errors + ["queue must be a list"]
    seen_ids: set[str] = set()
    seen_ranks: set[int] = set()
    score_keys: list[tuple[int, float, float, str]] = []
    ranked_count = 0
    unscored_count = 0
    for index, entry in enumerate(queue):
        path = f"queue[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{path} must be an object")
            continue
        card_id = entry.get("cardId")
        if not _text(card_id):
            errors.append(f"{path}.cardId must be non-empty")
        elif card_id in seen_ids:
            errors.append(f"{path}.cardId is duplicated: {card_id}")
        else:
            seen_ids.add(card_id)
        rank = entry.get("rank")
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            errors.append(f"{path}.rank must be a positive integer")
        elif rank in seen_ranks:
            errors.append(f"{path}.rank is duplicated: {rank}")
        else:
            seen_ranks.add(rank)
        expected_score, known_weight = _priority(entry, path, errors, weights)
        priority = entry.get("priority") if isinstance(entry.get("priority"), dict) else {}
        score = priority.get("score")
        confidence = priority.get("confidence")
        if expected_score is not None and _number(score) and abs(float(score) - expected_score) > 0.02:
            errors.append(f"{path}.priority.score does not match the weighted dimensions")
        confidence_value = float(confidence) if _number(confidence) else 0.0
        if not math.isclose(confidence_value, known_weight, abs_tol=0.02):
            errors.append(f"{path}.priority.confidence does not match known signal weight")
        if score is None:
            unscored_count += 1
            score_keys.append((1, 0.0, 0.0, str(card_id)))
        elif _number(score) and _number(confidence):
            ranked_count += 1
            score_keys.append((0, -float(score), -float(confidence), str(card_id)))
        else:
            score_keys.append((1, 0.0, 0.0, str(card_id)))
    if seen_ranks and seen_ranks != set(range(1, len(queue) + 1)):
        errors.append("queue ranks must be consecutive starting at 1")
    if score_keys and score_keys != sorted(score_keys):
        errors.append("queue must use descending score, descending confidence, then ascending cardId")

    if not isinstance(result.get("reviewOrder"), list):
        errors.append("reviewOrder must be a list")
    elif result["reviewOrder"] != [entry.get("cardId") for entry in queue if isinstance(entry, dict)]:
        errors.append("reviewOrder must match queue card IDs")
    if not isinstance(result.get("reviewQueue"), dict):
        errors.append("reviewQueue must be an object")
    elif result["reviewQueue"].get("cardIds") != [entry.get("cardId") for entry in queue if isinstance(entry, dict)]:
        errors.append("reviewQueue.cardIds must match queue card IDs")

    summary = result.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object")
    else:
        expected_counts = {
            "queueCount": len(queue),
            "rankedCount": ranked_count,
            "unscoredCount": unscored_count,
        }
        for field, expected in expected_counts.items():
            if summary.get(field) != expected:
                errors.append(f"summary.{field}={summary.get(field)} does not match {expected}")
        eligible_count = summary.get("eligibleCardCount", len(queue))
        if not isinstance(eligible_count, int) or isinstance(eligible_count, bool):
            errors.append("summary.eligibleCardCount must be an integer")
        elif eligible_count < len(queue):
            errors.append("summary.eligibleCardCount cannot be smaller than queueCount")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a sort priority projection.")
    parser.add_argument("result", type=Path)
    args = parser.parse_args(argv)
    try:
        result = json.loads(args.result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_result(result)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated {len(result['queue'])} priority card(s) in {result['mode']} mode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
