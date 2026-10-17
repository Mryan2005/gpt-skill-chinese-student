"""Compare finding fingerprints between fix rounds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def fingerprint(finding: dict[str, Any]) -> str:
    return "|".join(
        str(finding.get(field, "")) for field in ("code", "entityId", "rootLayer")
    )


def _findings(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict) and isinstance(value.get("findings"), list):
        return [item for item in value["findings"] if isinstance(item, dict)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    raise ValueError("input must be a finding report or finding list")


def compare_findings(previous: Any, current: Any) -> dict[str, Any]:
    previous_ids = {fingerprint(item) for item in _findings(previous)}
    current_ids = {fingerprint(item) for item in _findings(current)}
    remaining = sorted(current_ids)
    return {
        "previousCount": len(previous_ids),
        "currentCount": len(current_ids),
        "resolved": sorted(previous_ids - current_ids),
        "remaining": remaining,
        "new": sorted(current_ids - previous_ids),
        "noProgress": previous_ids == current_ids,
        "reduced": len(current_ids) < len(previous_ids),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare check finding fingerprints.")
    parser.add_argument("previous", type=Path)
    parser.add_argument("current", type=Path)
    args = parser.parse_args()
    previous = json.loads(args.previous.read_text(encoding="utf-8"))
    current = json.loads(args.current.read_text(encoding="utf-8"))
    print(json.dumps(compare_findings(previous, current), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
