"""Build a bounded, evidence-backed exam-driven heal coordination report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MAX_ROUNDS = 5
OWNERS = {"check", "fix", "learn", "amend"}
EVIDENCE_STATUSES = {"supported", "needs_verification", "rejected"}
OPTIMIZATION_STATUSES = {"APPLIED", "RECOMMENDED", "NO_OP", "BLOCKED"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _count(value: Any) -> bool:
    return isinstance(value, int) and value >= 0


def _metrics(value: Any) -> bool:
    return isinstance(value, dict) and all(_count(value.get(field)) for field in ("readableQuestions", "coveredQuestions", "mappedQuestions", "completeSolutions", "formulaComplete", "sourceComplete", "retrievalSuccess", "unresolvedQuestions"))


def _meaningful_progress(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    return any(current[field] > previous[field] for field in ("coveredQuestions", "mappedQuestions", "completeSolutions", "formulaComplete", "sourceComplete", "retrievalSuccess")) or current["unresolvedQuestions"] < previous["unresolvedQuestions"]


def _hit_progress(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    previous_counts = previous.get("counts", {})
    current_counts = current.get("counts", {})
    return current_counts.get("HIT", 0) > previous_counts.get("HIT", 0) or any(current_counts.get(status, 0) < previous_counts.get(status, 0) for status in ("PARTIAL", "MISS", "UNRESOLVED"))


def _opposite(left: str, right: str) -> bool:
    return {left, right} == {"merge", "split"}


def _optimization_oscillation(rounds: list[dict[str, Any]]) -> bool:
    history: list[tuple[set[str], str, bool]] = []
    for round_data in rounds:
        for action in round_data.get("optimizationActions", []):
            if not isinstance(action, dict):
                continue
            operation = str(action.get("operation", action.get("type", ""))).casefold()
            if "merge" in operation:
                operation = "merge"
            elif "split" in operation:
                operation = "split"
            else:
                continue
            targets = {str(value) for value in action.get("targetIds", [])}
            history.append((targets, operation, bool(action.get("newEvidenceRefs"))))
    for previous, current in zip(history, history[1:]):
        if previous[0] and previous[0] == current[0] and _opposite(previous[1], current[1]) and not current[2]:
            return True
    return False


def choose_stop(rounds: list[dict[str, Any]], max_rounds: int) -> tuple[str, str]:
    if not rounds:
        return "CONTINUE", "No evaluation round has been recorded yet."
    latest = rounds[-1]
    if latest.get("regressions") or latest.get("regression", {}).get("detected") is True:
        return "STOP_REGRESSION", "A repair introduced a validated regression."
    if latest.get("optimizationStability", {}).get("oscillationDetected") is True or _optimization_oscillation(rounds):
        return "STOP_OPTIMIZATION_OSCILLATION", "Opposite optimization operations targeted the same entities without new evidence."
    if latest.get("blockedItems") or latest.get("blocker", {}).get("blocked") is True:
        return "STOP_BLOCKED", latest.get("blocker", {}).get("reason", "Evidence or permission blocked the next repair.")
    if latest.get("overfit", {}).get("answerOnlyImprovement") is True:
        return "STOP_OVERFIT_RISK", "Observed improvement is answer-only and is not supported by holdout or knowledge-structure improvement."
    if latest.get("reEvaluation", {}).get("unresolvedQuestions") == 0:
        return "CONVERGED", "No unresolved evaluable question remains."
    if len(rounds) >= max_rounds:
        return "MAX_ROUNDS_REACHED", f"The configured maximum of {max_rounds} rounds was reached."
    if len(rounds) >= 2 and not any(_meaningful_progress(rounds[index - 1]["reEvaluation"], rounds[index]["reEvaluation"]) or _hit_progress(rounds[index - 1].get("examHitAfter", {}), rounds[index].get("examHitAfter", {})) for index in range(1, len(rounds))):
        return "STOP_STALLED", "Two consecutive rounds produced no meaningful material improvement."
    return "CONTINUE", "Continue while the next repair has evidence and expected measurable progress."


def _validate_hit_summary(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors: list[str] = []
    for field in ("reportPath", "reportSha256", "snapshotId", "snapshotContentSha256"):
        if not _text(value.get(field)):
            errors.append(f"{path}.{field} must be non-empty")
    if value.get("selectionPolicy") != "all_questions":
        errors.append(f"{path}.selectionPolicy must be all_questions")
    counts = value.get("counts")
    statuses = ("HIT", "PARTIAL", "MISS", "UNRESOLVED")
    if not isinstance(counts, dict) or any(not isinstance(counts.get(status), int) or counts.get(status) < 0 for status in statuses):
        errors.append(f"{path}.counts must contain non-negative HIT/PARTIAL/MISS/UNRESOLVED")
    elif not isinstance(value.get("totalQuestions"), int) or value["totalQuestions"] != sum(counts[status] for status in statuses):
        errors.append(f"{path}.totalQuestions must equal Hit status counts")
    return errors


def validate_input(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != "heal.exam-driven.input.v1":
        errors.append("schemaVersion must be heal.exam-driven.input.v1")
    for field in ("healRunId", "subjectId", "examPdfPath"):
        if not _text(data.get(field)):
            errors.append(f"{field} must be non-empty")
    if data.get("ocrUsed") is not False or data.get("delegatedOcr") is not False:
        errors.append("native PDF reading requires ocrUsed=false and delegatedOcr=false")
    if not isinstance(data.get("baseline"), dict) or not _metrics(data["baseline"]):
        errors.append("baseline metrics are incomplete")
    errors.extend(_validate_hit_summary(data.get("examHit"), "examHit"))
    split = data.get("split")
    if not isinstance(split, dict) or not isinstance(split.get("iterationQuestionIds"), list) or not isinstance(split.get("holdoutQuestionIds"), list):
        errors.append("split must contain iterationQuestionIds and holdoutQuestionIds")
    elif set(split["iterationQuestionIds"]) & set(split["holdoutQuestionIds"]):
        errors.append("iteration and holdout sets must be disjoint")
    web = data.get("webResearch", {"requested": False, "available": False, "performed": False})
    if not isinstance(web, dict) or any(not isinstance(web.get(field, False), bool) for field in ("requested", "available", "performed")):
        errors.append("webResearch flags are invalid")
    supplements = data.get("externalSupplements", [])
    if not isinstance(supplements, list):
        errors.append("externalSupplements must be a list")
    else:
        for index, supplement in enumerate(supplements):
            if not isinstance(supplement, dict):
                errors.append(f"externalSupplements[{index}] must be an object")
                continue
            for field in ("supplementId", "sourceUrl", "sourceTitle", "publisher", "accessedAt", "provenanceType", "evidenceStatus"):
                if not _text(supplement.get(field)):
                    errors.append(f"externalSupplements[{index}].{field} must be non-empty")
            if not str(supplement.get("sourceUrl", "")).startswith(("https://", "http://")):
                errors.append(f"externalSupplements[{index}].sourceUrl must be an http(s) URL")
            if supplement.get("provenanceType") != "external_supplement":
                errors.append(f"externalSupplements[{index}].provenanceType must be external_supplement")
            if supplement.get("evidenceStatus") not in EVIDENCE_STATUSES:
                errors.append(f"externalSupplements[{index}].evidenceStatus is invalid")
            if not isinstance(supplement.get("supportedClaims"), list) or not supplement["supportedClaims"]:
                errors.append(f"externalSupplements[{index}].supportedClaims must be non-empty")
    return errors


def build_report(data: dict[str, Any]) -> dict[str, Any]:
    errors = validate_input(data)
    if errors:
        raise ValueError("; ".join(errors))
    requested_max_rounds = int(data.get("maxRounds", MAX_ROUNDS))
    if not 1 <= requested_max_rounds <= MAX_ROUNDS:
        raise ValueError(f"maxRounds must be between 1 and {MAX_ROUNDS}")
    max_rounds = requested_max_rounds
    rounds = data.get("rounds", [])
    if not isinstance(rounds, list) or len(rounds) > max_rounds:
        raise ValueError("rounds must be a list with at most maxRounds entries")
    normalized_rounds: list[dict[str, Any]] = []
    for index, round_data in enumerate(rounds, start=1):
        if not isinstance(round_data, dict) or round_data.get("round") != index:
            raise ValueError("round numbers must be continuous")
        if not _metrics(round_data.get("evaluation")) or not _metrics(round_data.get("reEvaluation")):
            raise ValueError(f"round {index} metrics are incomplete")
        for field in ("repairActions", "knowledgeEnrichmentActions", "optimizationActions", "regressions", "blockedItems"):
            if not isinstance(round_data.get(field), list):
                raise ValueError(f"round {index} {field} must be a list")
            if field in {"repairActions", "knowledgeEnrichmentActions"} and any(isinstance(action, dict) and action.get("owner") == "heal" for action in round_data[field]):
                raise ValueError(f"round {index} cannot invoke heal recursively")
        for gate_name in ("checkBefore", "checkAfter"):
            gate = round_data.get(gate_name)
            if not isinstance(gate, dict) or gate.get("readOnly") is not True or gate.get("consumesRound") is not False or not _text(gate.get("status")):
                raise ValueError(f"round {index} {gate_name} must be a non-consuming read-only check")
        if round_data.get("optimizationRunCount") != 1 or round_data.get("optimizationStatus") not in OPTIMIZATION_STATUSES:
            raise ValueError(f"round {index} must contain exactly one optimization phase")
        for field in ("coverageDelta", "qualityDelta"):
            delta = round_data.get(field)
            if not isinstance(delta, dict) or "before" not in delta or "after" not in delta:
                raise ValueError(f"round {index} {field} must contain before and after")
        stability = round_data.get("optimizationStability")
        if not isinstance(stability, dict) or not isinstance(stability.get("oscillationDetected"), bool) or not isinstance(stability.get("newEvidenceRefs"), list):
            raise ValueError(f"round {index} optimizationStability is incomplete")
        if stability["oscillationDetected"] and not round_data.get("regressions") and round_data.get("stopDecision", {}).get("decision") not in {"STOP", "BLOCK"}:
            raise ValueError(f"round {index} oscillation must stop or block")
        stop_decision = round_data.get("stopDecision")
        if not isinstance(stop_decision, dict) or not _text(stop_decision.get("decision")) or not _text(stop_decision.get("reason")):
            raise ValueError(f"round {index} stopDecision is incomplete")
        hit_errors = _validate_hit_summary(round_data.get("examHitAfter"), f"round {index} examHitAfter")
        if hit_errors:
            raise ValueError("; ".join(hit_errors))
        for repair in round_data.get("repairPlan", []):
            if repair.get("owner") not in OWNERS:
                raise ValueError(f"round {index} has an invalid repair owner")
            if repair.get("answerOnly") is True:
                raise ValueError(f"round {index} cannot use an answer-only repair")
        normalized_rounds.append(round_data)
    stop_reason, stop_detail = choose_stop(normalized_rounds, max_rounds)
    status = "HEALED" if stop_reason == "CONVERGED" else "CONTINUE" if stop_reason == "CONTINUE" else "PARTIAL"
    return {
        "schemaVersion": "heal.exam-driven.report.v1",
        "healRunId": data["healRunId"],
        "mode": "exam-driven",
        "command": data.get("command", "exam"),
        "subjectId": data["subjectId"],
        "status": status,
        "maxRounds": max_rounds,
        "input": {"examPdfPath": data["examPdfPath"], "examPdfSha256": data.get("examPdfSha256"), "ocrUsed": False, "delegatedOcr": False, "sourceImmutable": True},
        "baseline": data["baseline"],
        "examHitBaseline": data["examHit"],
        "split": data["split"],
        "webResearch": data.get("webResearch", {"requested": False, "available": False, "performed": False}),
        "externalSupplements": data.get("externalSupplements", []),
        "readOnlyChecks": data.get("readOnlyChecks", {
            "initial": {"status": "NOT_RECORDED", "readOnly": True, "consumesRound": False},
            "final": {"status": "NOT_RECORDED", "readOnly": True, "consumesRound": False},
        }),
        "rounds": normalized_rounds,
        "stop": {"reason": stop_reason, "detail": stop_detail},
        "sourceMutation": False,
        "examResultMutation": False,
        "learnerModelMutation": False,
        "answerOnlyRepair": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an exam-driven heal report.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = build_report(json.loads(args.input.read_text(encoding="utf-8")))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "reportStatus": report["status"], "stop": report["stop"]}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
