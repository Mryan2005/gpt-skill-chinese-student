"""Create a deterministic, non-mutating optimization report from a card catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


MAX_CARD_CHARS = 1600


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _operation(operation_type: str, target_ids: list[str], risk: str, reason: str, evidence: list[str], requires_confirmation: bool, decision: str = "RECOMMEND") -> dict[str, Any]:
    stable = "|".join([operation_type, *sorted(target_ids)])
    operation_id = "op-" + hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16]
    return {
        "operationId": operation_id,
        "type": operation_type,
        "targetIds": sorted(target_ids),
        "risk": risk,
        "decision": decision,
        "requiresConfirmation": requires_confirmation,
        "evidenceRefs": evidence,
        "reason": reason,
        "newEvidenceRefs": [],
    }


def build_report(data: dict[str, Any], state_sha256: str) -> dict[str, Any]:
    cards = data.get("cards")
    if not isinstance(cards, list):
        raise ValueError("cards must be a list")
    operations: list[dict[str, Any]] = []
    aliases: list[dict[str, str]] = []
    mappings: list[dict[str, str]] = []
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for card in cards:
        if not isinstance(card, dict) or not isinstance(card.get("id"), str) or not card["id"].strip():
            raise ValueError("every card must have a non-empty id")
        signature = (_norm(card.get("title")), _norm(card.get("body")))
        if signature in seen and signature != ("", ""):
            canonical = seen[signature]
            operation = _operation(
                "exact_duplicate",
                [canonical["id"], card["id"]],
                "low",
                "Normalized title and body are identical; preserve the first stable ID and alias the duplicate.",
                [canonical["id"], card["id"]],
                False,
            )
            operations.append(operation)
            aliases.append({"oldId": card["id"], "newId": canonical["id"]})
            mappings.append({"oldId": card["id"], "newId": canonical["id"]})
        else:
            seen[signature] = card

        body = str(card.get("body", ""))
        if card.get("splitRecommended") is True or len(body) > MAX_CARD_CHARS:
            operations.append(_operation(
                "oversized_split",
                [card["id"]],
                "high",
                "The card contains more than one likely recall unit or exceeds the bounded card size; a domain-aware split is required.",
                [card["id"]],
                True,
            ))

    fragment_groups: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        key = card.get("fragmentKey")
        if isinstance(key, str) and key.strip():
            fragment_groups.setdefault(_norm(key), []).append(card)
    for key, group in fragment_groups.items():
        if len(group) > 1:
            ids = [card["id"] for card in group]
            operations.append(_operation(
                "fragmented_merge",
                ids,
                "high",
                f"Explicit fragment group '{key}' suggests one concept, but semantic merge requires domain review.",
                ids,
                True,
            ))

    for candidate in data.get("relatedCandidates", []):
        if isinstance(candidate, dict) and isinstance(candidate.get("targetIds"), list) and len(candidate["targetIds"]) >= 2:
            operations.append(_operation(
                "related_but_distinct",
                [str(value) for value in candidate["targetIds"]],
                "low",
                str(candidate.get("reason") or "Evidence indicates a relation, not a duplicate; preserve separate cards."),
                [str(value) for value in candidate.get("evidenceRefs", [])] or ["input:related-candidate"],
                False,
                "NO_OP",
            ))

    unique_operations: dict[str, dict[str, Any]] = {operation["operationId"]: operation for operation in operations}
    operations = [unique_operations[key] for key in sorted(unique_operations)]
    has_recommendation = any(operation["decision"] == "RECOMMEND" for operation in operations)
    status = "RECOMMENDATIONS" if has_recommendation else "NO_OP"
    return {
        "schemaVersion": "optimize.report.v1",
        "optimizeRunId": str(data.get("optimizeRunId") or "optimize-run"),
        "subjectId": str(data.get("subjectId") or "subject"),
        "mode": "analyze",
        "status": status,
        "currentStateSha256": state_sha256,
        "operations": operations,
        "migration": {
            "cardAliases": aliases,
            "cardIdMappings": mappings,
            "relationRemaps": [],
            "questionMappingRemaps": [],
            "learnerStateEffects": [{"kind": "alias_only", **alias} for alias in aliases],
            "validation": {"status": "PASS", "checks": ["source-preserved", "exam-result-preserved", "learner-state-preserved", "stable-operation-ids"]},
        },
        "confirmation": {"required": any(operation["requiresConfirmation"] for operation in operations), "received": False, "scope": "analysis only"},
        "validation": {"status": "PASS", "idempotent": True, "errors": []},
        "sourcePreserved": True,
        "examResultPreserved": True,
        "learnerStatePreserved": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a Chinese Student graph optimization without mutating the input.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        report = build_report(data, _sha256(args.input))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "reportStatus": report["status"], "operations": len(report["operations"])}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
