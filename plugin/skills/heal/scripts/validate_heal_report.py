"""Validate a bounded check-fix convergence report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STATUSES = {"SUCCESS", "STOPPED", "BLOCKED", "FAILED"}
CHECK_RESULTS = {"FAIL", "PASS", "PASS_WITH_WARNINGS", "BLOCKED"}
FIX_STATUSES = {"COMPLETE", "PARTIAL", "FAILED", "BLOCKED"}
SEVERITIES = ("blocker", "error", "warning", "info")


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _summary(value: Any, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} must be an object"]
    return [f"{path}.{field} must be a non-negative integer" for field in SEVERITIES if not _non_negative_int(value.get(field))]


def _check_round(check: Any, round_number: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(check, dict):
        return [f"rounds[{round_number - 1}].check must be an object"]
    for field in ("checkRunId", "artifactVersion", "artifactHash"):
        if not _text(check.get(field)):
            errors.append(f"rounds[{round_number - 1}].check.{field} must be non-empty")
    if check.get("result") != "FAIL":
        errors.append(f"rounds[{round_number - 1}].check.result must be FAIL before a fix")
    errors.extend(_summary(check.get("summary"), f"rounds[{round_number - 1}].check.summary"))
    if not isinstance(check.get("findingFingerprints"), list) or any(not _text(item) for item in check["findingFingerprints"]):
        errors.append(f"rounds[{round_number - 1}].check.findingFingerprints must contain strings")
    return errors


def validate_report(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["report must be an object"]
    errors: list[str] = []
    if report.get("schemaVersion") != "heal.report.v1":
        errors.append("schemaVersion must be heal.report.v1")
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
        checker = roles.get("checker")
        fixer = roles.get("fixer")
        if not isinstance(checker, dict) or checker.get("readOnly") is not True or checker.get("reusedAgent") is not True:
            errors.append("checker must be reused and read-only")
        if not isinstance(fixer, dict) or fixer.get("writeEnabled") is not True or fixer.get("reusedAgent") is not True:
            errors.append("fixer must be reused and write-enabled")

    errors.extend(_summary(report.get("initialSummary"), "initialSummary"))
    errors.extend(_summary(report.get("finalSummary"), "finalSummary"))

    previous_after_hash: str | None = None
    for index, item in enumerate(rounds):
        path = f"rounds[{index}]"
        expected_round = index + 1
        if not isinstance(item, dict) or item.get("round") != expected_round:
            errors.append(f"{path}.round must be {expected_round}")
            continue
        errors.extend(_check_round(item.get("check"), expected_round))
        check = item.get("check") if isinstance(item.get("check"), dict) else {}
        fix = item.get("fix")
        if not isinstance(fix, dict):
            errors.append(f"{path}.fix is required")
        else:
            for field in ("fixRunId", "artifactHashBefore", "artifactHashAfter"):
                if not _text(fix.get(field)):
                    errors.append(f"{path}.fix.{field} must be non-empty")
            if fix.get("fixRound") != expected_round or fix.get("basedOnCheckRound") != expected_round:
                errors.append(f"{path}.fix must be based on the same check round")
            if _text(check.get("artifactHash")) and fix.get("artifactHashBefore") != check.get("artifactHash"):
                errors.append(f"STALE_CHECK_REPORT: {path}.fix.artifactHashBefore differs from check artifactHash")
            if fix.get("status") not in FIX_STATUSES:
                errors.append(f"{path}.fix.status is invalid")
            if fix.get("sourceMutation") is not False:
                errors.append(f"{path}.fix.sourceMutation must be false")
            validation = fix.get("localValidation")
            if not isinstance(validation, dict) or validation.get("status") not in {"PASS", "FAIL"}:
                errors.append(f"{path}.fix.localValidation.status must be PASS or FAIL")
            if not isinstance(fix.get("escalations"), list):
                errors.append(f"{path}.fix.escalations must be a list")
            previous_after_hash = fix.get("artifactHashAfter") if _text(fix.get("artifactHashAfter")) else previous_after_hash
        progress = item.get("progress")
        if not isinstance(progress, dict):
            errors.append(f"{path}.progress is required")
        else:
            for field in ("resolved", "persisted", "new", "regressed"):
                if not _non_negative_int(progress.get(field)):
                    errors.append(f"{path}.progress.{field} must be a non-negative integer")
            if not isinstance(progress.get("noProgress"), bool):
                errors.append(f"{path}.progress.noProgress must be boolean")
            elif progress.get("noProgress") and progress.get("resolved") != 0:
                errors.append(f"{path}.progress.noProgress cannot have resolved findings")

    final = report.get("finalCheck")
    if not isinstance(final, dict):
        errors.append("finalCheck is required")
    else:
        for field in ("checkRunId", "artifactVersion", "artifactHash"):
            if not _text(final.get(field)):
                errors.append(f"finalCheck.{field} must be non-empty")
        if final.get("round") != len(rounds) + 1:
            errors.append("finalCheck.round must be roundsExecuted + 1")
        if final.get("result") not in CHECK_RESULTS:
            errors.append("finalCheck.result is invalid")
        errors.extend(_summary(final.get("summary"), "finalCheck.summary"))
        if not isinstance(final.get("findingFingerprints"), list) or any(not _text(item) for item in final["findingFingerprints"]):
            errors.append("finalCheck.findingFingerprints must contain strings")
        if previous_after_hash is not None and final.get("artifactHash") != previous_after_hash:
            errors.append("finalCheck.artifactHash must match the last fix artifactHashAfter")

    final_summary = report.get("finalSummary")
    if isinstance(final_summary, dict) and isinstance(final, dict) and final_summary != final.get("summary"):
        errors.append("finalSummary must equal finalCheck.summary")
    if report.get("status") == "SUCCESS" and isinstance(final, dict):
        summary = final.get("summary", {})
        if final.get("result") not in {"PASS", "PASS_WITH_WARNINGS"} or summary.get("blocker") != 0 or summary.get("error") != 0:
            errors.append("SUCCESS requires a clean PASS or PASS_WITH_WARNINGS final check")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a heal report.")
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
