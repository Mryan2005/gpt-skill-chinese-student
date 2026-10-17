"""Verify that a check report still describes the current artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def verify_report(
    report: Any,
    *,
    artifact_version: str,
    artifact_hash: str,
    schema_version: str = "check.finding.v1",
) -> list[str]:
    if not isinstance(report, dict):
        return ["STALE_CHECK_REPORT: report must be an object"]
    artifact = report.get("artifact")
    errors: list[str] = []
    if report.get("schemaVersion") != schema_version:
        errors.append("STALE_CHECK_REPORT: schemaVersion mismatch")
    if not isinstance(artifact, dict):
        return errors + ["STALE_CHECK_REPORT: artifact is missing"]
    checks = {
        "artifact.version": (artifact.get("version"), artifact_version),
        "artifact.hash": (artifact.get("hash"), artifact_hash),
    }
    for field, (observed, expected) in checks.items():
        if not _text(observed) or observed != expected:
            errors.append(f"STALE_CHECK_REPORT: {field} mismatch")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify check report freshness before fix.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--artifact-version", required=True)
    parser.add_argument("--artifact-hash", required=True)
    parser.add_argument("--schema-version", default="check.finding.v1")
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = verify_report(
        report,
        artifact_version=args.artifact_version,
        artifact_hash=args.artifact_hash,
        schema_version=args.schema_version,
    )
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print("PASS: check report matches the current artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
