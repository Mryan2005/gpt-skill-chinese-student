"""Plan check execution without making agent creation a business dependency."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PLUGIN_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(PLUGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SCRIPTS))

from agent_roles import load_agent_role_registry, validate_agent_role_registry  # noqa: E402

MAX_PARALLEL = 3
MAX_CONSECUTIVE_SPAWN_FAILURES = 2


def _load_bundles() -> dict[str, list[str]]:
    plugin_root = Path(__file__).resolve().parents[3]
    registry = load_agent_role_registry(plugin_root)
    errors = validate_agent_role_registry(registry, plugin_root)
    if errors:
        raise ValueError("invalid Agent Role Registry: " + " | ".join(errors))
    workflow = next(item for item in registry["workflows"] if item["skill"] == "check")
    return {name: list(role_ids) for name, role_ids in workflow["bundles"].items()}


BUNDLES = _load_bundles()


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def plan_execution(available_slots: int, consecutive_spawn_failures: int = 0) -> dict[str, Any]:
    if available_slots < 0:
        raise ValueError("available_slots must be non-negative")
    if consecutive_spawn_failures < 0:
        raise ValueError("consecutive_spawn_failures must be non-negative")

    spawning_disabled = consecutive_spawn_failures >= MAX_CONSECUTIVE_SPAWN_FAILURES
    if spawning_disabled or available_slots == 0:
        mode = "orchestrator-fallback"
        max_parallel = 0
        batches = [list(BUNDLES)]
        reason = "spawn-failure-threshold" if spawning_disabled else "no-agent-capacity"
    else:
        max_parallel = min(MAX_PARALLEL, available_slots)
        if max_parallel >= 3:
            mode = "parallel-agent"
            batches = _chunks(list(BUNDLES), max_parallel)
        elif max_parallel == 2:
            mode = "batched-agent"
            batches = [["structure", "domain"], ["presentation", "coverage"]]
        else:
            mode = "shared-agent"
            batches = [list(BUNDLES)]
        if consecutive_spawn_failures:
            reason = "prior-spawn-failure"
        else:
            reason = None

    return {
        "requestedMode": "multi-agent",
        "actualMode": mode,
        "maxParallel": max_parallel,
        "maxConsecutiveSpawnFailures": MAX_CONSECUTIVE_SPAWN_FAILURES,
        "spawnFailures": consecutive_spawn_failures,
        "spawningDisabled": spawning_disabled,
        "fallbackReason": reason,
        "batches": batches,
        "bundles": BUNDLES,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan check auditor execution.")
    parser.add_argument("--available-slots", type=int, required=True)
    parser.add_argument("--consecutive-spawn-failures", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(plan_execution(args.available_slots, args.consecutive_spawn_failures), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
