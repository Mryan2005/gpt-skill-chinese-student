"""Apply evidence-backed, idempotent recovery attempts to a derived Hit report."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_recovery_tasks import build_tasks
from validate_exam_hit_stage import validate_report


RECOVERY_SCHEMA = "exam.hit.recovery.v1"
RECOVERABLE_METHODS = {"native_pdf_visual_recheck", "source_cross_check", "mapping_recheck", "card_content_recheck"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_attempt(attempt: Any, task: dict[str, Any]) -> list[str]:
    if not isinstance(attempt, dict):
        return [f"{task['taskId']}: recovery attempt must be an object"]
    errors: list[str] = []
    for field in ("attemptId", "questionId", "action", "status", "attemptedAt", "method"):
        if not _text(attempt.get(field)):
            errors.append(f"{task['taskId']}: attempt.{field} must be non-empty")
    if attempt.get("questionId") != task["questionId"]:
        errors.append(f"{task['taskId']}: attempt questionId mismatch")
    if attempt.get("action") != task["nextAction"]:
        errors.append(f"{task['taskId']}: attempt action does not match nextAction")
    if attempt.get("status") not in {"RECOVERED", "BLOCKED", "NO_CHANGE"}:
        errors.append(f"{task['taskId']}: attempt status is invalid")
    if attempt.get("method") not in RECOVERABLE_METHODS:
        errors.append(f"{task['taskId']}: recovery method is invalid")
    evidence = attempt.get("evidenceRefs")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{task['taskId']}: attempt evidenceRefs must be non-empty")
    if attempt.get("method") == "native_pdf_visual_recheck":
        if attempt.get("ocrUsed") is not False or attempt.get("delegatedOcr") is not False or attempt.get("intermediateTextSources") != []:
            errors.append(f"{task['taskId']}: native PDF recovery cannot use OCR or intermediate text")
    result = attempt.get("result")
    if attempt.get("status") == "RECOVERED":
        if not isinstance(result, dict) or not isinstance(result.get("hitResult"), dict):
            errors.append(f"{task['taskId']}: RECOVERED attempt requires result.hitResult")
    return errors


def run_recovery(hit_report: dict[str, Any], ledger: dict[str, Any] | None = None, attempts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    errors = validate_report(hit_report)
    if errors:
        raise ValueError("invalid Hit report: " + "; ".join(errors))
    ledger = copy.deepcopy(ledger) if ledger is not None else build_tasks(hit_report)
    if ledger.get("schemaVersion") != RECOVERY_SCHEMA:
        raise ValueError("ledger must be exam.hit.recovery.v1")
    tasks = ledger.get("tasks", [])
    task_map = {task.get("questionId"): task for task in tasks if isinstance(task, dict)}
    results = copy.deepcopy(hit_report.get("questionResults", []))
    result_map = {item.get("questionId"): item for item in results if isinstance(item, dict)}
    attempts = attempts or []
    by_question = {attempt.get("questionId"): attempt for attempt in attempts if isinstance(attempt, dict)}
    recovered: list[str] = []
    blocked: list[str] = []
    errors_out: list[str] = []
    for question_id, attempt in by_question.items():
        task = task_map.get(question_id)
        if not task:
            errors_out.append(f"unknown question recovery attempt: {question_id}")
            continue
        if any(existing.get("attemptId") == attempt.get("attemptId") for existing in task.get("attempts", []) if isinstance(existing, dict)):
            continue
        errors_out.extend(_validate_attempt(attempt, task))
        if errors_out:
            continue
        task.setdefault("attempts", []).append(copy.deepcopy(attempt))
        task["lastAttemptId"] = attempt["attemptId"]
        task["updatedAt"] = attempt["attemptedAt"]
        if attempt["status"] == "RECOVERED":
            result = result_map.get(question_id)
            recovered_result = attempt["result"]["hitResult"]
            if result is None:
                errors_out.append(f"missing question result for {question_id}")
                continue
            result["hitResult"] = copy.deepcopy(recovered_result)
            if "readStatus" in attempt["result"]:
                result["readStatus"] = attempt["result"]["readStatus"]
            task["status"] = "RECOVERED"
            recovered.append(question_id)
        elif attempt["status"] == "BLOCKED":
            task["status"] = "BLOCKED"
            blocked.append(question_id)
        else:
            task["status"] = "OPEN"
    if errors_out:
        raise ValueError("; ".join(errors_out))
    for task in tasks:
        if task.get("status") == "RECOVERED":
            task["status"] = "REVALIDATED" if task.get("questionId") in recovered else task["status"]
    recovered_report = copy.deepcopy(hit_report)
    recovered_report["examHitRunId"] = f"{hit_report['examHitRunId']}-recovered"
    recovered_report["derivedFromExamHitRunId"] = hit_report["examHitRunId"]
    recovered_report["recoveryStage"] = "recoveredHit"
    recovered_report["questionResults"] = results
    recovered_report["recoveryMetadata"] = {"originalHitReportHash": _sha256(hit_report), "recoveredQuestionIds": sorted(recovered), "blockedQuestionIds": sorted(blocked), "attemptCount": sum(len(task.get("attempts", [])) for task in tasks), "createdAt": _now()}
    # Counts are recomputed by the existing Hit report validator's contract; keep
    # the derived report structurally honest for downstream comparison.
    counts = {status: 0 for status in {"HIT", "PARTIAL", "MISS", "UNRESOLVED"}}
    for item in results:
        counts[item.get("hitResult", {}).get("hitStatus")] = counts.get(item.get("hitResult", {}).get("hitStatus"), 0) + 1
    summary = copy.deepcopy(hit_report.get("coverageSummary", {}))
    summary["counts"] = counts
    summary["totalQuestions"] = len(results)
    summary["determinateQuestions"] = len(results) - counts["UNRESOLVED"]
    summary["completeCoverageRate"] = counts["HIT"] / len(results) if results else 0
    summary["determinateCoverageRate"] = counts["HIT"] / summary["determinateQuestions"] if summary["determinateQuestions"] else None
    card_stats: dict[str, dict[str, Any]] = {}
    for item in results:
        result = item.get("hitResult", {})
        if result.get("hitStatus") not in {"HIT", "PARTIAL"}:
            continue
        for card_id in result.get("supportingCardIds", []):
            stats = card_stats.setdefault(card_id, {"HIT": 0, "PARTIAL": 0, "questionIds": []})
            stats[result["hitStatus"]] += 1
            stats["questionIds"].append(item.get("questionId"))
    summary["cardHitStatistics"] = [{"cardId": card_id, **stats} for card_id, stats in sorted(card_stats.items())]
    summary["derivedFocusFromObservedHits"] = [card_id for card_id, stats in sorted(card_stats.items(), key=lambda pair: (-pair[1]["HIT"], -pair[1]["PARTIAL"], pair[0])) if stats["HIT"] > 0]
    recovered_report["coverageSummary"] = summary
    recovered_report["auditStatus"] = "COMPLETE" if counts["UNRESOLVED"] == 0 else "PARTIAL"
    recovered_errors = validate_report(recovered_report)
    if recovered_errors:
        raise ValueError("recovered Hit report is invalid: " + "; ".join(recovered_errors))
    ledger["checkpoint"] = {"completedTaskIds": sorted(task["taskId"] for task in tasks if task.get("status") in {"REVALIDATED", "BLOCKED"}), "remainingTaskIds": sorted(task["taskId"] for task in tasks if task.get("status") not in {"REVALIDATED", "BLOCKED"}), "updatedAt": _now(), "resumable": True}
    return {"schemaVersion": RECOVERY_SCHEMA, "originalHit": hit_report, "recoveredHit": recovered_report, "ledger": ledger, "sourceMutation": False, "examResultMutation": False, "learnerModelMutation": False}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run idempotent Exam Hit recovery tasks.")
    parser.add_argument("--hit-report", type=Path, required=True)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--attempts", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        hit_report = json.loads(args.hit_report.read_text(encoding="utf-8"))
        ledger = json.loads(args.ledger.read_text(encoding="utf-8")) if args.ledger else None
        attempts = json.loads(args.attempts.read_text(encoding="utf-8")) if args.attempts else []
        if not isinstance(attempts, list):
            raise ValueError("attempts must be a JSON list")
        output = run_recovery(hit_report, ledger, attempts)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "recovery-report.v1.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.output_dir / "recovered-hit-report.json").write_text(json.dumps(output["recoveredHit"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.output_dir / "recovery-ledger.json").write_text(json.dumps(output["ledger"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "recovered": output["recoveredHit"]["recoveryMetadata"]["recoveredQuestionIds"], "remaining": output["ledger"]["checkpoint"]["remainingTaskIds"]}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
