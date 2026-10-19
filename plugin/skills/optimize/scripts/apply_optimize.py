"""Apply only safe exact-duplicate aliases from a current optimize plan."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from validate_optimize_report import validate_report


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _replace_id(value: Any, aliases: dict[str, str]) -> Any:
    if isinstance(value, str):
        return aliases.get(value, value)
    if isinstance(value, list):
        return [_replace_id(item, aliases) for item in value]
    if isinstance(value, dict):
        return {key: _replace_id(item, aliases) if key in {"cardId", "primaryCardId", "secondaryCardIds", "sourceCardId", "targetCardId", "from", "to"} else item for key, item in value.items()}
    return value


def apply_report(record: dict[str, Any], report: dict[str, Any], confirmed: bool = False) -> dict[str, Any]:
    errors = validate_report(report)
    if errors:
        raise ValueError("invalid optimize report: " + "; ".join(errors))
    if not confirmed:
        raise ValueError("explicit confirmation is required to apply an optimize plan")
    if report.get("mode") not in {"analyze", "apply"}:
        raise ValueError("the report is not an applyable plan")
    applied = [operation for operation in report.get("operations", []) if operation.get("type") == "exact_duplicate" and operation.get("decision") in {"RECOMMEND", "APPROVE", "APPLIED"}]
    unsupported = [operation for operation in report.get("operations", []) if operation.get("type") != "exact_duplicate" and operation.get("decision") in {"RECOMMEND", "APPROVE", "APPLIED"}]
    if unsupported:
        raise ValueError("high-risk or semantic operations require a complete domain migration plan")
    result = copy.deepcopy(record)
    aliases: dict[str, str] = {}
    cards_by_id = {card.get("id"): card for card in result.get("cards", []) if isinstance(card, dict)}
    planned_aliases = {
        item.get("oldId"): item.get("newId")
        for item in report.get("migration", {}).get("cardAliases", [])
        if isinstance(item, dict) and item.get("oldId") and item.get("newId")
    }
    for operation in applied:
        target_ids = [target_id for target_id in operation.get("targetIds", []) if target_id in cards_by_id]
        if len(target_ids) != 2:
            raise ValueError(f"exact duplicate operation has missing targets: {operation.get('operationId')}")
        planned_duplicate = next((target_id for target_id in target_ids if planned_aliases.get(target_id) in target_ids), None)
        duplicate = planned_duplicate or sorted(target_ids)[1]
        canonical = planned_aliases.get(duplicate) or next(target_id for target_id in target_ids if target_id != duplicate)
        aliases[duplicate] = canonical
    result["cards"] = [card for card in result.get("cards", []) if not (isinstance(card, dict) and card.get("id") in aliases)]
    result["relations"] = _replace_id(result.get("relations", []), aliases)
    result["questionMappings"] = _replace_id(result.get("questionMappings", []), aliases)
    result["cardAliases"] = {**result.get("cardAliases", {}), **aliases}
    # Learner evidence is intentionally not rewritten; aliases keep historical references resolvable.
    if result.get("learnerState") != record.get("learnerState"):
        raise ValueError("Learner State changed during optimization")
    if result.get("source") != record.get("source") or result.get("examResult") != record.get("examResult"):
        raise ValueError("Source or Exam Result changed during optimization")
    return {
        "record": result,
        "status": "APPLIED" if applied else "NO_OP",
        "appliedOperationIds": [operation["operationId"] for operation in applied],
        "aliases": aliases,
        "highRiskPending": [operation["operationId"] for operation in unsupported],
        "sourcePreserved": True,
        "examResultPreserved": True,
        "learnerStatePreserved": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply safe exact-duplicate aliases from an optimize report.")
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
        report = json.loads(args.report.read_text(encoding="utf-8"))
        if report.get("currentStateSha256") != _sha256(args.record):
            raise ValueError("optimization plan is stale; current state fingerprint changed")
        result = apply_report(record, report, args.confirm)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result["record"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in result.items() if key != "record"}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"APPLY_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
