"""Validate review-input.v2 routing manifests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_review_input(manifest: Any) -> list[str]:
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    errors: list[str] = []
    if manifest.get("schemaVersion") != "review-input.v2":
        errors.append("schemaVersion must be review-input.v2")
    if manifest.get("reviewMode") not in {"exam-result", "user-written"}:
        errors.append("reviewMode must be exam-result or user-written")
    if not _text(manifest.get("reviewRunId")):
        errors.append("reviewRunId must be non-empty")
    policy = manifest.get("outputPolicy")
    if not isinstance(policy, dict) or policy.get("generatesPdf") is not False:
        errors.append("review must not generate PDF")
    if manifest.get("reviewMode") == "exam-result":
        if not _text(manifest.get("examResultPath")):
            errors.append("exam-result mode requires examResultPath")
        if manifest.get("learnerModelWriteAllowed") is not False:
            errors.append("exam-result mode cannot write Learner Model")
        if manifest.get("attemptId") is not None:
            errors.append("exam-result mode must not invent attemptId")
    if manifest.get("reviewMode") == "user-written":
        if not _text(manifest.get("attemptId")):
            errors.append("user-written mode requires a new attemptId")
        if manifest.get("answererType") != "human":
            errors.append("user-written mode requires answererType human")
        if manifest.get("learnerModelWriteAllowed") is not True or policy.get("writesLearnerModel") is not True:
            errors.append("user-written mode may write only eligible learner evidence")
        sources = manifest.get("sources")
        if not isinstance(sources, list) or {item.get("role") for item in sources if isinstance(item, dict)} != {"questions", "answers", "user-submission"}:
            errors.append("user-written mode requires questions, answers, and user-submission sources")
        else:
            for index, source in enumerate(sources):
                if source.get("source") != "original_pdf" or source.get("ocrUsed") is not False or source.get("delegatedOcr") is not False or source.get("intermediateTextSources") != []:
                    errors.append(f"sources[{index}] violates native PDF reading contract")
    pipeline = manifest.get("reviewPipeline")
    if pipeline is not None:
        expected_stages = {"pdf", "highlight", "gap_detection", "research", "learn_handoff", "recheck", "report"}
        if not isinstance(pipeline, list) or not expected_stages.issubset(set(pipeline)) or not any(stage in pipeline for stage in ("consume_exam_hit", "consume_or_delegate_exam_hit")):
            errors.append("reviewPipeline must consume or delegate Exam Hit before highlighting")
    research_policy = manifest.get("researchPolicy")
    if research_policy is not None and (research_policy.get("allowed") is not True or research_policy.get("requiresProvenance") is not True):
        errors.append("researchPolicy must allow only provenance-backed supplements")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a review routing manifest.")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_review_input(value)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print("PASS: validated review routing manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
