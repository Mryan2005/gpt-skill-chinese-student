"""Validate predeclared Chinese Student agent-role contracts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_roles import load_agent_role_registry, validate_agent_role_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Chinese Student Agent Role Registry.")
    parser.add_argument("--plugin-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    plugin_root = args.plugin_root.resolve()
    try:
        registry = load_agent_role_registry(plugin_root)
    except (OSError, ValueError) as exc:
        print(f"AGENT_ROLE_REGISTRY_ERROR: {exc}", file=sys.stderr)
        return 1
    errors = validate_agent_role_registry(registry, plugin_root)
    if errors:
        for error in errors:
            print(f"AGENT_ROLE_REGISTRY_ERROR: {error}", file=sys.stderr)
        return 1
    workflow_count = len(registry["workflows"])
    role_count = sum(len(workflow["roles"]) for workflow in registry["workflows"])
    print(f"PASS: {role_count} role contracts across {workflow_count} workflows are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
