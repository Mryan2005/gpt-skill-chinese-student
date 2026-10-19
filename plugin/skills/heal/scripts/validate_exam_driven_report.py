"""Validate an exam-driven heal coordination report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MAX_ROUNDS = 5


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_supplement(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors: list[str] = []
    for field in ("supplementId", "sourceUrl", "sourceTitle", "publisher", "accessedAt", "provenanceType", "evidenceStatus"):
        if not _text(value.get(field)):
            errors.append(f"{path}.{field} must be non-empty")
    if not str(value.get("sourceUrl", "")).startswith(("https://", "http://")):
        errors.append(f"{path}.sourceUrl must be an http(s) URL")
    if value.get("provenanceType") != "external_supplement":
        errors.append(f"{path}.provenanceType must be external_supplement")
    if value.get("evidenceStatus") not in {"supported", "needs_verification", "rejected"}:
        errors.append(f"{path}.evidenceStatus is invalid")
    if not isinstance(value.get("supportedClaims"), list) or not value["supportedClaims"]:
        errors.append(f"{path}.supportedClaims must be non-empty")
    return errors


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
        errors.append(f"{path}.counts are incomplete")
    elif not isinstance(value.get("totalQuestions"), int) or value["totalQuestions"] != sum(counts[status] for status in statuses):
        errors.append(f"{path}.totalQuestions does not equal status counts")
    return errors


def _check_gate(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors: list[str] = []
    if value.get("readOnly") is not True:
        errors.append(f"{path}.readOnly must be true")
    if value.get("consumesRound") is not False:
        errors.append(f"{path}.consumesRound must be false")
    if not _text(value.get("status")):
        errors.append(f"{path}.status must be non-empty")
    return errors


def _round_protocol(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    errors: list[str] = []
    errors.extend(_check_gate(value.get("checkBefore"), f"{path}.checkBefore"))
    errors.extend(_check_gate(value.get("checkAfter"), f"{path}.checkAfter"))
    for field in ("repairActions", "knowledgeEnrichmentActions", "optimizationActions", "regressions", "blockedItems"):
        if not isinstance(value.get(field), list):
            errors.append(f"{path}.{field} must be a list")
        elif field in {"repairActions", "knowledgeEnrichmentActions"}:
            for action in value[field]:
                if isinstance(action, dict) and action.get("owner") == "heal":
                    errors.append(f"{path}.{field} cannot invoke heal recursively")
    if value.get("optimizationRunCount") != 1:
        errors.append(f"{path}.optimizationRunCount must be exactly 1")
    if value.get("optimizationStatus") not in {"APPLIED", "RECOMMENDED", "NO_OP", "BLOCKED"}:
        errors.append(f"{path}.optimizationStatus is invalid")
    for field in ("coverageDelta", "qualityDelta"):
        delta = value.get(field)
        if not isinstance(delta, dict) or "before" not in delta or "after" not in delta:
            errors.append(f"{path}.{field} must contain before and after")
    decision = value.get("stopDecision")
    if not isinstance(decision, dict) or not _text(decision.get("decision")) or not _text(decision.get("reason")):
        errors.append(f"{path}.stopDecision must contain decision and reason")
    stability = value.get("optimizationStability")
    if not isinstance(stability, dict) or not isinstance(stability.get("oscillationDetected"), bool) or not isinstance(stability.get("newEvidenceRefs"), list):
        errors.append(f"{path}.optimizationStability is incomplete")
    elif stability["oscillationDetected"] and value.get("stopDecision", {}).get("decision") not in {"STOP", "BLOCK"}:
        errors.append(f"{path}.optimizationStability requires a stop or block decision")
    for action in value.get("optimizationActions", []):
        if not isinstance(action, dict):
            errors.append(f"{path}.optimizationActions contains a non-object")
            continue
        if action.get("owner") not in {None, "optimize"}:
            errors.append(f"{path}.optimizationActions has an invalid owner")
        if action.get("answerOnly") is True:
            errors.append(f"{path}.optimizationActions cannot be answer-only")
    return errors


def validate_report(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") != "heal.exam-driven.report.v1":
        errors.append("schemaVersion is invalid")
    if report.get("mode") != "exam-driven":
        errors.append("mode must be exam-driven")
    if report.get("status") not in {"HEALED", "CONTINUE", "PARTIAL", "BLOCKED", "STALLED"}:
        errors.append("status is invalid")
    if not _text(report.get("healRunId")) or not _text(report.get("subjectId")):
        errors.append("healRunId and subjectId must be non-empty")
    if not isinstance(report.get("maxRounds"), int) or not 1 <= report["maxRounds"] <= MAX_ROUNDS:
        errors.append(f"maxRounds must be between 1 and {MAX_ROUNDS}")
    for field in ("sourceMutation", "examResultMutation", "learnerModelMutation", "answerOnlyRepair"):
        if report.get(field) is not False:
            errors.append(f"{field} must be false")
    input_data = report.get("input")
    if not isinstance(input_data, dict) or not _text(input_data.get("examPdfPath")) or input_data.get("ocrUsed") is not False or input_data.get("delegatedOcr") is not False or input_data.get("sourceImmutable") is not True:
        errors.append("input violates native PDF/source immutability contract")
    web = report.get("webResearch")
    if not isinstance(web, dict) or any(not isinstance(web.get(field, False), bool) for field in ("requested", "available", "performed")):
        errors.append("webResearch flags are invalid")
    supplements = report.get("externalSupplements")
    if not isinstance(supplements, list):
        errors.append("externalSupplements must be a list")
    else:
        for index, supplement in enumerate(supplements):
            errors.extend(_validate_supplement(supplement, f"externalSupplements[{index}]"))
    split = report.get("split")
    if not isinstance(split, dict) or not isinstance(split.get("iterationQuestionIds"), list) or not isinstance(split.get("holdoutQuestionIds"), list):
        errors.append("split is incomplete")
    elif set(split["iterationQuestionIds"]) & set(split["holdoutQuestionIds"]):
        errors.append("iteration and holdout sets overlap")
    errors.extend(_validate_hit_summary(report.get("examHitBaseline"), "examHitBaseline"))
    rounds = report.get("rounds")
    if not isinstance(rounds, list) or len(rounds) > report.get("maxRounds", MAX_ROUNDS):
        errors.append("rounds exceed maxRounds")
    else:
        for index, round_data in enumerate(rounds, start=1):
            if not isinstance(round_data, dict) or round_data.get("round") != index:
                errors.append(f"round {index} is not continuous")
                continue
            errors.extend(_round_protocol(round_data, f"rounds[{index - 1}]"))
            errors.extend(_validate_hit_summary(round_data.get("examHitAfter"), f"rounds[{index - 1}].examHitAfter"))
            for repair in round_data.get("repairPlan", []):
                if repair.get("owner") not in {"check", "fix", "learn", "amend"}:
                    errors.append(f"round {index} has an invalid repair owner")
                if repair.get("answerOnly") is True:
                    errors.append(f"round {index} contains answer-only repair")
    read_only_checks = report.get("readOnlyChecks")
    if not isinstance(read_only_checks, dict):
        errors.append("readOnlyChecks is required")
    else:
        errors.extend(_check_gate(read_only_checks.get("initial"), "readOnlyChecks.initial"))
        errors.extend(_check_gate(read_only_checks.get("final"), "readOnlyChecks.final"))
    stop = report.get("stop")
    if not isinstance(stop, dict) or not _text(stop.get("reason")) or not _text(stop.get("detail")):
        errors.append("stop is incomplete")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an exam-driven heal report.")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_report(report)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print("PASS: validated exam-driven heal report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
