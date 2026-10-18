"""Hash the immutable Exam Result before and after review."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify that an Exam Result was not mutated.")
    parser.add_argument("result", type=Path)
    parser.add_argument("--before", required=True)
    args = parser.parse_args()
    try:
        after = file_hash(args.result)
    except OSError as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    if after != args.before:
        print(f"REVIEW_MUTATED_EXAM_RESULT: before={args.before} after={after}", file=sys.stderr)
        return 1
    print(f"PASS: Exam Result unchanged {after}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
