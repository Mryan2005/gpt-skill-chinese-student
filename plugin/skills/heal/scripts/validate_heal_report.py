"""Validate a cold-start learning-experience heal report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STATUSES = {"HEALED", "HEALED_WITH_WARNINGS", "STALLED", "BLOCKED", "MAX_ROUNDS_REACHED"}
DECISIONS = {"ACCEPT", "REFINE", "REJECT", "BLOCKED"}
SEVERITIES = ("blocker", "error", "warning", "info")


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _summary(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    return [f"{path}.{field} must be a non-negative integer" for field in SEVERITIES if not _non_negative_int(value.get(field))]


def _pedagogy(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    coverage = value.get("understandingCoverage")
    if not isinstance(coverage, (int, float)) or isinstance(coverage, bool) or not 0 <= coverage <= 1:
        errors.append(f"{path}.understandingCoverage must be between 0 and 1")
    for field in ("deadEnds", "highFriction", "mediumFriction", "unresolvedNotUnderstood", "missingPrerequisites", "redundancyCandidates"):
        if not _non_negative_int(value.get(field)):
            errors.append(f"{path}.{field} must be a non-negative integer")
    return errors


def validate_report(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") != "heal.report.v2":
        errors.append("schemaVersion must be heal.report.v2")
    for field in ("healRunId", "stopReason"):
        if not _text(report.get(field)):
            errors.append(f"{field} must be non-empty")
    if report.get("status") not in STATUSES:
        errors.append("status is invalid")
    max_rounds = report.get("maxRounds")
    if not _non_negative_int(max_rounds) or not 1 <= max_rounds <= 10:
        errors.append("maxRounds must be between 1 and 10")
    rounds = report.get("rounds")
    if not isinstance(rounds, list):
        errors.append("rounds must be a list")
        rounds = []
    if report.get("roundsExecuted") != len(rounds):
        errors.append("roundsExecuted must equal rounds length")
    if _non_negative_int(max_rounds) and len(rounds) > max_rounds:
        errors.append("rounds cannot exceed maxRounds")

    workspace = report.get("workspace")
    if not isinstance(workspace, dict):
        errors.append("workspace is required")
    else:
        if workspace.get("root") != ".heal/current":
            errors.append("workspace.root must be .heal/current")
        if workspace.get("previousRunDeleted") is not True:
            errors.append("workspace.previousRunDeleted must be true")
        if workspace.get("cleanVerified") is not True:
            errors.append("workspace.cleanVerified must be true")
        if workspace.get("residualPaths") != []:
            errors.append("HEAL_WORKSPACE_NOT_CLEAN: residualPaths must be empty")

    roles = report.get("roles")
    if not isinstance(roles, dict):
        errors.append("roles is required")
    else:
        novice = roles.get("novice")
        maintainer = roles.get("maintainer")
        if not isinstance(novice, dict) or any(novice.get(field) is not True for field in ("readOnly", "coldStart", "synthetic", "userFacingOnly")):
            errors.append("novice must be read-only, cold-start, synthetic, and user-facing-only")
        if not isinstance(maintainer, dict) or maintainer.get("writeEnabled") is not True or maintainer.get("reusedAgent") is not True:
            errors.append("maintainer must be reused and write-enabled")

    errors.extend(_pedagogy(report.get("initialPedagogy"), "initialPedagogy"))
    errors.extend(_pedagogy(report.get("finalPedagogy"), "finalPedagogy"))

    for index, item in enumerate(rounds):
        path = f"rounds[{index}]"
        expected = index + 1
        if not isinstance(item, dict) or item.get("round") != expected:
            errors.append(f"{path}.round must be {expected}")
            continue
        novice = item.get("novice")
        if not isinstance(novice, dict):
            errors.append(f"{path}.novice is required")
        else:
            for field in ("traceId", "tracePath", "artifactVersion"):
                if not _text(novice.get(field)):
                    errors.append(f"{path}.novice.{field} must be non-empty")
            for field in ("freshContext", "completedLearningPath"):
                if novice.get(field) is not True:
                    errors.append(f"{path}.novice.{field} must be true")
            if novice.get("externalKnowledgeUsed") is not False:
                errors.append(f"{path}.novice.externalKnowledgeUsed must be false")
            value = novice.get("understandingCoverage")
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                errors.append(f"{path}.novice.understandingCoverage must be between 0 and 1")
            for field in ("deadEnds", "highFriction", "mediumFriction", "unresolvedNotUnderstood"):
                if not _non_negative_int(novice.get(field)):
                    errors.append(f"{path}.novice.{field} must be a non-negative integer")
            fingerprints = novice.get("frictionFingerprints")
            if not isinstance(fingerprints, list) or any(not _text(value) for value in fingerprints):
                errors.append(f"{path}.novice.frictionFingerprints must contain strings")

        maintainer = item.get("maintainer")
        if not isinstance(maintainer, dict):
            errors.append(f"{path}.maintainer is required")
        else:
            if not isinstance(maintainer.get("evaluationPath"), list) or not maintainer["evaluationPath"]:
                errors.append(f"{path}.maintainer.evaluationPath must be non-empty")
            decisions = maintainer.get("decisions")
            if not isinstance(decisions, list):
                errors.append(f"{path}.maintainer.decisions must be a list")
            else:
                for decision in decisions:
                    if not isinstance(decision, dict) or decision.get("decision") not in DECISIONS or not _text(decision.get("reason")):
                        errors.append(f"{path}.maintainer.decisions contains an invalid decision")
            if maintainer.get("sourceMutation") is not False:
                errors.append(f"{path}.maintainer.sourceMutation must be false")
            if maintainer.get("learnerModelMutation") is not False:
                errors.append(f"{path}.maintainer.learnerModelMutation must be false")
            if maintainer.get("syntheticDataPersisted") is not False:
                errors.append(f"{path}.maintainer.syntheticDataPersisted must be false")
            validation = maintainer.get("localValidation")
            if not isinstance(validation, dict) or validation.get("status") not in {"PASS", "FAIL"}:
                errors.append(f"{path}.maintainer.localValidation.status must be PASS or FAIL")
        progress = item.get("progress")
        if not isinstance(progress, dict):
            errors.append(f"{path}.progress is required")
        else:
            for field in ("resolvedPedagogical", "persisted", "new", "regressed"):
                if not _non_negative_int(progress.get(field)):
                    errors.append(f"{path}.progress.{field} must be a non-negative integer")
            if not isinstance(progress.get("noProgress"), bool):
                errors.append(f"{path}.progress.noProgress must be boolean")

    final_check = report.get("finalTechnicalCheck")
    if final_check is not None:
        if not isinstance(final_check, dict) or final_check.get("result") not in {"PASS", "PASS_WITH_WARNINGS", "FAIL", "BLOCKED"}:
            errors.append("finalTechnicalCheck.result is invalid")
        elif final_check.get("summary") is not None:
            errors.extend(_summary(final_check["summary"], "finalTechnicalCheck.summary"))

    final_pedagogy = report.get("finalPedagogy", {})
    if report.get("status") == "HEALED" and any(final_pedagogy.get(field) != 0 for field in ("deadEnds", "highFriction", "unresolvedNotUnderstood")):
        errors.append("HEALED requires no dead ends, high friction, or unresolved NOT_UNDERSTOOD findings")
    if report.get("status") == "HEALED_WITH_WARNINGS" and any(final_pedagogy.get(field) != 0 for field in ("deadEnds", "highFriction", "unresolvedNotUnderstood")):
        errors.append("HEALED_WITH_WARNINGS requires no blocking pedagogical friction")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a cold-start learning-experience heal report.")
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
    print(f"PASS: validated heal report {report['healRunId']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
