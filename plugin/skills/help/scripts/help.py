"""Render a read-only, registry-backed Chinese Student command reference."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(PLUGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SCRIPTS))

from skill_registry import load_registry as load_skill_registry  # noqa: E402
from skill_registry import validate_registry as validate_skill_registry  # noqa: E402


def _skill_dirs(skills_root: Path) -> set[str]:
    return {path.name for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)[1]
    values: dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line.strip())
        if match:
            values[match.group(1)] = match.group(2).strip().strip('"\'')
    return values


def load_registry(help_root: Path, skills_root: Path) -> dict[str, Any]:
    registry = json.loads((help_root / "references" / "command-index.json").read_text(encoding="utf-8"))
    commands = registry.get("commands", [])
    actual = _skill_dirs(skills_root)
    indexed = {item.get("name") for item in commands if isinstance(item, dict)}
    missing = sorted(actual - indexed)
    stale = sorted(indexed - actual)
    if missing or stale:
        raise ValueError(f"help command index is out of sync; missing={missing}; stale={stale}")
    plugin_root = skills_root.parent
    routing = load_skill_registry(plugin_root)
    routing_errors = validate_skill_registry(routing, plugin_root)
    if routing_errors:
        raise ValueError("skill route registry is invalid: " + " | ".join(routing_errors))
    routing_by_name = {item.get("id"): item for item in routing.get("commands", [])}
    for item in commands:
        if item.get("kind") == "workflow":
            metadata = skills_root / item["name"] / "agents" / "openai.yaml"
            if not metadata.is_file():
                raise ValueError(f"workflow {item['name']} has no agents/openai.yaml")
        frontmatter = _frontmatter(skills_root / item["name"] / "SKILL.md")
        if frontmatter.get("name") != item["name"]:
            raise ValueError(f"help index name mismatch for {item['name']}")
        route_entry = routing_by_name.get(item["name"])
        if not route_entry or route_entry.get("kind") != item.get("kind"):
            raise ValueError(f"help/route kind mismatch for {item['name']}")
    return registry


def validate_registry(help_root: Path, skills_root: Path) -> list[str]:
    try:
        load_registry(help_root, skills_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]
    return []


def _command_table(commands: list[dict[str, Any]]) -> str:
    lines = ["### Chinese Student — Command Reference", "", "| Command | Kind | Status | Description |", "| --- | --- | --- | --- |"]
    for item in commands:
        lines.append(f"| `chinese-student: {item['name']}` | {item['kind']} | {item['status']} | {item['description']} |" )
    lines.extend(["", "Usage: `chinese-student: help <command>`", ""])
    return "\n".join(lines)


def _subcommand_name(subcommand: Any) -> str:
    return str(subcommand.get("name", "")) if isinstance(subcommand, dict) else str(subcommand)


def _detail(item: dict[str, Any], subcommand: str | None = None) -> str:
    lines = [f"### chinese-student: {item['name']}", "", item["description"], "", "**Kind:** `" + item["kind"] + "`  ", "**Status:** `" + item["status"] + "`", "", "**Usage**"]
    lines.extend(f"- `{usage}`" for usage in item.get("usage", []))
    lines.extend(["", "**Default behavior / inputs**", f"- Inputs: {'；'.join(item.get('inputs', []))}", f"- Outputs: {'；'.join(item.get('outputs', []))}", f"- Data impact: {'；'.join(item.get('sideEffects', []))}", f"- Confirmation: {item.get('confirmation', 'none')}"])
    subcommands = item.get("subcommands", [])
    if subcommands:
        lines.extend(["", "**Subcommands**"])
        for sub in subcommands:
            if subcommand and _subcommand_name(sub) != subcommand:
                continue
            if isinstance(sub, dict):
                lines.append(f"- `{sub['name']}`: {sub['description']}")
                if sub.get("inputs"):
                    lines.append(f"  - Inputs: {'；'.join(sub['inputs'])}")
                if sub.get("outputs"):
                    lines.append(f"  - Outputs: {'；'.join(sub['outputs'])}")
                if sub.get("sideEffects"):
                    lines.append(f"  - Data impact: {'；'.join(sub['sideEffects'])}")
                if sub.get("confirmation"):
                    lines.append(f"  - Confirmation: {sub['confirmation']}")
            else:
                lines.append(f"- `{sub}`")
    if subcommand and not any(_subcommand_name(sub) == subcommand for sub in subcommands):
        supported = ", ".join(_subcommand_name(sub) for sub in subcommands) or "none"
        lines.append(f"\nUnknown subcommand `{subcommand}`. Supported: {supported}")
    lines.extend(["", "**Examples**"])
    lines.extend(f"- `{example}`" for example in item.get("examples", []))
    return "\n".join(lines)


def render_help(registry: dict[str, Any], command: str | None = None, subcommand: str | None = None, all_commands: bool = False) -> str:
    commands = registry["commands"]
    if command is None or all_commands:
        return _command_table(commands) if not all_commands else "\n\n".join(_detail(item) for item in commands)
    item = next((entry for entry in commands if entry["name"] == command), None)
    if item is None:
        suggestion = difflib.get_close_matches(command, [entry["name"] for entry in commands], n=1)
        return f"Unknown Chinese Student command `{command}`." + (f" Did you mean `{suggestion[0]}`?" if suggestion else "")
    return _detail(item, subcommand)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the Chinese Student command reference.")
    parser.add_argument("command", nargs="?")
    parser.add_argument("subcommand", nargs="?")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    help_root = Path(__file__).resolve().parents[1]
    skills_root = help_root.parent
    errors = validate_registry(help_root, skills_root)
    if errors:
        print("HELP_INDEX_ERROR: " + " | ".join(errors), file=sys.stderr)
        return 1
    registry = load_registry(help_root, skills_root)
    if args.json:
        print(json.dumps(registry, ensure_ascii=False, indent=2))
    else:
        all_commands = args.all or args.command == "all"
        print(render_help(registry, None if all_commands else args.command, args.subcommand, all_commands))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
