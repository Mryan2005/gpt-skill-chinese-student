"""Plan check execution without making agent creation a business dependency."""

from __future__ import annotations

import argparse
import json
from typing import Any


MAX_PARALLEL = 3
MAX_CONSECUTIVE_SPAWN_FAILURES = 2
BUNDLES = {
    "structure": ["structure", "source", "provenance", "question"],
    "domain": ["content", "solution", "math", "relation"],
    "presentation": ["latex", "rendering", "retrieval"],
    "coverage": ["coverage", "readiness", "learner-model", "sort-state"],
}


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
