from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "optimize"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from apply_optimize import apply_report  # noqa: E402
from plan_optimize import build_report  # noqa: E402
from validate_optimize_report import validate_report  # noqa: E402


class OptimizeStructureTests(unittest.TestCase):
    def test_skill_and_example_exist(self) -> None:
        self.assertTrue((SKILL_ROOT / "SKILL.md").is_file())
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "optimize-contract.md").is_file())
        self.assertTrue((SKILL_ROOT / "playbooks" / "analyze.md").is_file())
        report = json.loads((SKILL_ROOT / "examples" / "optimize-report.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_report(report), [])

    def test_analyze_detects_duplicate_split_fragment_and_distinct_candidates(self) -> None:
        report = build_report({
            "optimizeRunId": "run-1",
            "subjectId": "math-1",
            "cards": [
                {"id": "card:a", "title": "A", "body": "Same", "sourceIds": ["source:a"]},
                {"id": "card:b", "title": "A", "body": "Same", "sourceIds": ["source:a"]},
                {"id": "card:large", "title": "Large", "body": "x" * 1700},
                {"id": "card:fragment-1", "title": "Fragment 1", "body": "One", "fragmentKey": "topic"},
                {"id": "card:fragment-2", "title": "Fragment 2", "body": "Two", "fragmentKey": "topic"},
                {"id": "card:related-1", "title": "Related 1", "body": "One"},
                {"id": "card:related-2", "title": "Related 2", "body": "Two"}
            ],
            "relatedCandidates": [{"targetIds": ["card:related-1", "card:related-2"], "evidenceRefs": ["relation:related"], "reason": "Different recall cores."}]
        }, "sha256:test")
        self.assertEqual(validate_report(report), [])
        types = {operation["type"] for operation in report["operations"]}
        self.assertIn("exact_duplicate", types)
        self.assertIn("oversized_split", types)
        self.assertIn("fragmented_merge", types)
        self.assertIn("related_but_distinct", types)
        self.assertTrue(all(operation["evidenceRefs"] for operation in report["operations"]))

    def test_apply_exact_duplicate_preserves_protected_layers_and_is_idempotent(self) -> None:
        record = {
            "cards": [
                {"id": "card:a", "title": "A", "body": "Same"},
                {"id": "card:b", "title": "A", "body": "Same"}
            ],
            "relations": [{"from": "card:b", "to": "card:a", "type": "supports"}],
            "questionMappings": [{"questionId": "q1", "primaryCardId": "card:b"}],
            "cardAliases": {},
            "source": {"sha256": "source"},
            "examResult": {"attemptId": "attempt-1"},
            "learnerState": {"mastery": [{"cardId": "card:b", "status": "weak"}]}
        }
        report = build_report({"optimizeRunId": "run-2", "subjectId": "math-1", "cards": record["cards"]}, "sha256:test")
        report["confirmation"] = {"required": False, "received": True, "scope": "exact duplicate alias"}
        before_protected = {key: copy.deepcopy(record[key]) for key in ("source", "examResult", "learnerState")}
        result = apply_report(record, report, confirmed=True)
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(result["record"]["cardAliases"], {"card:b": "card:a"})
        self.assertEqual(result["record"]["questionMappings"][0]["primaryCardId"], "card:a")
        self.assertEqual({key: result["record"][key] for key in before_protected}, before_protected)
        second = build_report({"optimizeRunId": "run-3", "subjectId": "math-1", "cards": result["record"]["cards"]}, "sha256:next")
        self.assertFalse(any(operation["type"] == "exact_duplicate" for operation in second["operations"]))

    def test_high_risk_operations_require_confirmation(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "optimize-report.json").read_text(encoding="utf-8"))
        report["operations"][1]["requiresConfirmation"] = False
        errors = validate_report(report)
        self.assertTrue(any("high-risk" in error for error in errors))

    def test_protected_layer_mutation_is_rejected(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "optimize-report.json").read_text(encoding="utf-8"))
        report["learnerStatePreserved"] = False
        self.assertTrue(any("learnerStatePreserved" in error for error in validate_report(report)))


if __name__ == "__main__":
    unittest.main()
