"""Validate that the help index covers every live Skill directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from help import load_registry, validate_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Chinese Student help registry.")
    parser.add_argument("--help-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    skills_root = args.help_root.parent
    errors = validate_registry(args.help_root, skills_root)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print("PASS: help index covers all live skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
