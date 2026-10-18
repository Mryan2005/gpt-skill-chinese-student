"""Render an annotation overlay as a readable Markdown view without mutating Source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def render_markdown(overlay: dict[str, Any]) -> str:
    annotations = sorted(overlay.get("annotations", []), key=lambda item: (PRIORITY_ORDER.get(item.get("priority"), 9), item.get("targetId", "")))
    lines = [f"# Review highlights: {overlay.get('subjectId', 'unknown')}", "", "This overlay is derived review output. It does not modify the original Source.", ""]
    for item in annotations:
        lines.extend([
            f"## {item.get('priority', 'unknown').title()}: {item.get('targetId', 'unknown')}",
            f"- Type: `{item.get('highlightType', 'unknown')}`",
            f"- Evidence strength: `{item.get('evidenceStrength', 'unknown')}`",
            f"- Reason: {item.get('reason', '')}",
            f"- Evidence: {', '.join(item.get('evidenceRefs', []))}",
            f"- Next action: {item.get('actionHint', 'Review the linked evidence.')}",
            "",
        ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a review annotation overlay as Markdown.")
    parser.add_argument("overlay", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    overlay = json.loads(args.overlay.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(overlay), encoding="utf-8")
    print(f"WROTE: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
