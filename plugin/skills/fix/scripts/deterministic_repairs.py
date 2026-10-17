"""Classify check findings before semantic repair planning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DETERMINISTIC_CODES = {
    "DUPLICATE_ENTITY_ID",
    "SEARCH_CONTROL_FAILURE",
    "RETRIEVAL_INDEX_MISSING",
    "ASSET_MISSING",
    "LATEX_SYNTAX_ERROR",
    "FORMULA_SYNTAX_ERROR",
    "SOURCE_REFERENCE_BROKEN",
    "CHECK_WORKSPACE_NOT_CLEAN",
}
ESCALATION_CODES = {
    "SOURCE_MUTATED",
    "SOURCE_MUTATED_BY_DERIVATION",
    "MATH_CONTENT_LOSS",
    "FORMULA_SOURCE_MISMATCH",
    "UPDATE_REQUIRED_BEFORE_EXAM",
}


def classify_findings(findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result = {"deterministic": [], "semantic": [], "escalate": []}
    for finding in findings:
        code = finding.get("code")
        if code in DETERMINISTIC_CODES:
            bucket = "deterministic"
        elif code in ESCALATION_CODES:
            bucket = "escalate"
        else:
            bucket = "semantic"
        result[bucket].append(finding)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify fix findings.")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    findings = report.get("findings", report) if isinstance(report, dict) else report
    print(json.dumps(classify_findings(findings), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
