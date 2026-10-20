"""Plan, persist, resume, and evidence-gate Chinese Student Auto runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from auto_engine import PLUGIN_ROOT, apply_step_result, build_plan, explain, initialize_run, load_run, refresh_state, validate_plan
from skill_registry import load_registry


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Chinese Student Auto orchestration state engine.")
    subparsers = parser.add_subparsers(dest="mode", required=True)
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--request", type=Path, required=True)
    plan_parser.add_argument("--workspace", type=Path, required=True)
    plan_parser.add_argument("--run-id")
    plan_parser.add_argument("--authorization", action="append", default=[])
    for mode in ("run", "resume", "status", "explain"):
        item = subparsers.add_parser(mode)
        item.add_argument("--workspace", type=Path, required=True)
        item.add_argument("--run-id", required=True)
        if mode == "run":
            item.add_argument("--step-result", type=Path)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    try:
        if args.mode == "plan":
            plan = build_plan(read_json(args.request), run_id=args.run_id)
            errors = validate_plan(plan, registry=load_registry(PLUGIN_ROOT))
            if errors:
                raise ValueError(" | ".join(errors))
            state = initialize_run(workspace, plan, authorizations=args.authorization)
            state = refresh_state(plan, state, workspace)
            save_state(workspace / ".auto" / plan["runId"] / "state.json", state)
            print(json.dumps({"plan": plan, "state": state, "dispatch": explain(plan, state)}, ensure_ascii=False, indent=2))
        else:
            plan, state, state_path = load_run(workspace, args.run_id)
            if args.mode == "run" and args.step_result:
                state = apply_step_result(workspace, args.run_id, read_json(args.step_result))
            else:
                state = refresh_state(plan, state, workspace)
                save_state(state_path, state)
            output = explain(plan, state) if args.mode == "explain" else state
            print(json.dumps(output, ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"AUTO_ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
