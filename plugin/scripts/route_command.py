"""Classify a natural-language request without invoking or mutating a Skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from skill_registry import load_registry, route_command, validate_registry, validate_route_result


def _plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_input(path: Path | None, text: str | None) -> dict[str, Any]:
    if path:
        return json.loads(path.read_text(encoding="utf-8"))
    return {"schemaVersion": "command-route-input.v1", "text": text or ""}


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a Chinese Student request without executing it.")
    parser.add_argument("text", nargs="?", help="Natural-language request to classify")
    parser.add_argument("--input", type=Path, help="JSON command-route-input.v1 file")
    parser.add_argument("--subject", help="Optional subject hint")
    args = parser.parse_args()

    payload = _read_input(args.input, args.text)
    if payload.get("schemaVersion") not in {None, "command-route-input.v1"}:
        print("ROUTE_INPUT_ERROR: schemaVersion must be command-route-input.v1", file=sys.stderr)
        return 2
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        print("ROUTE_INPUT_ERROR: text must be non-empty", file=sys.stderr)
        return 2

    plugin_root = _plugin_root()
    registry = load_registry(plugin_root)
    registry_errors = validate_registry(registry, plugin_root)
    if registry_errors:
        print("ROUTE_REGISTRY_ERROR: " + " | ".join(registry_errors), file=sys.stderr)
        return 1
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    subject = args.subject or context.get("subject")
    result = route_command(text, registry=registry, subject=subject)
    result_errors = validate_route_result(result)
    if result_errors:
        print("ROUTE_RESULT_ERROR: " + " | ".join(result_errors), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
