"""Safely reset one disposable .heal/current workspace."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def validate_target(raw_path: str) -> Path:
    target = Path(raw_path).expanduser().resolve()
    if target.name != "current" or target.parent.name != ".heal":
        raise ValueError("workspace must be an exact .heal/current directory")
    return target


def reset_workspace(target: Path, apply: bool) -> list[str]:
    residual = sorted(str(path.relative_to(target)) for path in target.rglob("*")) if target.exists() else []
    if not apply:
        return residual
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reset a disposable heal workspace.")
    parser.add_argument("--workspace", required=True, help="Exact absolute path to .heal/current")
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
        print("Use --apply only when starting a new heal run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
