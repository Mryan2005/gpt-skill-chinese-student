"""Validate the plugin's skill graph, metadata, help index, and route contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from skill_registry import load_registry, validate_registry


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$")
DISPLAY_RE = re.compile(r'^\s*display_name:\s*["\']([^"\']+)["\']', re.MULTILINE)


def _frontmatter(path: Path) -> dict[str, str]:
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        field = FIELD_RE.match(line.strip())
        if field:
            values[field.group(1)] = field.group(2).strip().strip('"\'')
    return values


def validate_plugin(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads((plugin_root / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"plugin.json: {exc}"]
    if manifest.get("name") != "chinese-student":
        errors.append("plugin.json name must be chinese-student")
    if not manifest.get("version"):
        errors.append("plugin.json version must be non-empty")
    if manifest.get("license") != "AGPL-3.0-or-later":
        errors.append("plugin.json license must be AGPL-3.0-or-later")

    try:
        registry = load_registry(plugin_root)
    except (OSError, json.JSONDecodeError) as exc:
        return errors + [f"skill registry: {exc}"]
    errors.extend(validate_registry(registry, plugin_root))

    skills_root = plugin_root / "skills"
    entries = {str(entry["id"]): entry for entry in registry.get("commands", []) if isinstance(entry, dict) and entry.get("id")}
    for skill_id, entry in sorted(entries.items()):
        skill_root = skills_root / skill_id
        frontmatter = _frontmatter(skill_root / "SKILL.md") if (skill_root / "SKILL.md").is_file() else {}
        if frontmatter.get("name") != skill_id:
            errors.append(f"{skill_id}: SKILL.md frontmatter name must match directory")
        if not frontmatter.get("description"):
            errors.append(f"{skill_id}: SKILL.md description must be non-empty")
        metadata_path = skill_root / "agents" / "openai.yaml"
        if not metadata_path.is_file():
            errors.append(f"{skill_id}: missing agents/openai.yaml")
            continue
        metadata = metadata_path.read_text(encoding="utf-8")
        display = DISPLAY_RE.search(metadata)
        if not display or display.group(1) != entry.get("pickerDisplayName"):
            errors.append(f"{skill_id}: picker display name does not match skill registry")
        if entry.get("combinedInvocation") not in metadata:
            errors.append(f"{skill_id}: default prompt must mention {entry.get('combinedInvocation')}")

    help_path = skills_root / "help" / "references" / "command-index.json"
    try:
        help_index = json.loads(help_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return errors + [f"help command index: {exc}"]
    help_commands = {str(item.get("name")): item for item in help_index.get("commands", []) if isinstance(item, dict) and item.get("name")}
    if set(help_commands) != set(entries):
        errors.append(f"help/registry mismatch; help-only={sorted(set(help_commands) - set(entries))}; registry-only={sorted(set(entries) - set(help_commands))}")
    for skill_id, entry in entries.items():
        help_entry = help_commands.get(skill_id)
        if help_entry and help_entry.get("kind") != entry.get("kind"):
            errors.append(f"{skill_id}: help kind and registry kind differ")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Chinese Student plugin structure and routing metadata.")
    parser.add_argument("--plugin-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate_plugin(args.plugin_root.resolve())
    if errors:
        for error in errors:
            print(f"PLUGIN_STRUCTURE_ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: plugin structure, skill metadata, help index, and route registry are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
