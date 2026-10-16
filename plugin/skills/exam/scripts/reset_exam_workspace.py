"""Safely reset one disposable .exam/current workspace.

The command is dry-run by default. Destructive deletion requires --apply and
the target must be an exact directory named current under a .exam directory.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def validate_target(raw_path: str) -> Path:
    target = Path(raw_path).expanduser().resolve()
    if target.name != "current" or target.parent.name != ".exam":
        raise ValueError("workspace must be an exact .exam/current directory")
    if target.parent.parent == target.parent or target.parent.parent == target:
        raise ValueError("workspace parent is invalid")
    return target


def reset_workspace(target: Path, apply: bool) -> list[str]:
    existing = sorted(str(path.relative_to(target)) for path in target.rglob("*")) if target.exists() else []
    if not apply:
        return existing
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reset one disposable exam workspace.")
    parser.add_argument("--workspace", required=True, help="Exact absolute path to .exam/current")
    parser.add_argument("--apply", action="store_true", help="Delete and recreate the workspace")
    args = parser.parse_args(argv)
    try:
        target = validate_target(args.workspace)
        residual = reset_workspace(target, args.apply)
    except (OSError, ValueError) as exc:
        print(f"RESET_ERROR: {exc}", file=sys.stderr)
        return 2
    if args.apply:
        print(f"RESET_APPLIED: {target}")
        print("RESIDUAL_PATHS: []")
    else:
        print(f"DRY_RUN: {target}")
        print(f"RESIDUAL_PATHS: {residual or []}")
        print("Use --apply only when starting a new exam run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
