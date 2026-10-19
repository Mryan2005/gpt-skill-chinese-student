from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "heal"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from reset_heal_workspace import reset_workspace, validate_target  # noqa: E402
from validate_heal_report import validate_report  # noqa: E402
from validate_learning_trace import validate_trace  # noqa: E402
from validate_exam_driven_report import validate_report as validate_exam_driven_report  # noqa: E402
from run_exam_driven import build_report as build_exam_driven_report, choose_stop  # noqa: E402


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class HealStructureTests(unittest.TestCase):
    def test_front_door_and_contract_exist(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 90)
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "heal-contract.md").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "run-state.md").is_file())
        self.assertTrue((SKILL_ROOT / "playbooks" / "exam-driven.md").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "exam-driven-contract.md").is_file())
        self.assertTrue((SKILL_ROOT / "scripts" / "run_exam_driven.py").is_file())

    def test_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"]
        documents += sorted((SKILL_ROOT / "references").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_heal_report_passes(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "heal-report.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_report(report), [])

    def test_learning_trace_passes(self) -> None:
        trace = json.loads((SKILL_ROOT / "examples" / "learning-trace.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_trace(trace), [])

    def test_exam_driven_report_passes(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-driven-report.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_exam_driven_report(report), [])

    def test_exam_driven_report_rejects_answer_only_repairs(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-driven-report.json").read_text(encoding="utf-8"))
        report["rounds"][0]["repairPlan"][0]["answerOnly"] = True
        errors = validate_exam_driven_report(report)
        self.assertTrue(any("answer-only" in error for error in errors))

    def test_exam_driven_report_accepts_explicit_external_supplement(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-driven-report.json").read_text(encoding="utf-8"))
        report["webResearch"] = {"requested": True, "available": True, "performed": True}
        report["externalSupplements"] = [{
            "supplementId": "supplement-demo-001",
            "sourceUrl": "https://example.edu/source",
            "sourceTitle": "Authoritative course note",
            "publisher": "Example University",
            "accessedAt": "2026-10-19T00:00:00+08:00",
            "relatedQuestionIds": ["series-mcq-17"],
            "relatedCardIds": ["ratio-test"],
            "supportedClaims": ["The ratio test is inconclusive when the ratio limit equals one."],
            "evidenceStatus": "supported",
            "provenanceType": "external_supplement"
        }]
        self.assertEqual(validate_exam_driven_report(report), [])

    def test_report_rejects_source_or_learner_mutation(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "heal-report.json").read_text(encoding="utf-8"))
        mutated = copy.deepcopy(report)
        mutated["rounds"][0]["maintainer"]["sourceMutation"] = True
        mutated["rounds"][0]["maintainer"]["learnerModelMutation"] = True
        errors = validate_report(mutated)
        self.assertTrue(any("sourceMutation" in error for error in errors))
        self.assertTrue(any("learnerModelMutation" in error for error in errors))

    def test_trace_rejects_external_knowledge(self) -> None:
        trace = json.loads((SKILL_ROOT / "examples" / "learning-trace.json").read_text(encoding="utf-8"))
        trace["externalKnowledgeUsed"] = True
        errors = validate_trace(trace)
        self.assertTrue(any("externalKnowledgeUsed" in error for error in errors))

    def test_report_rejects_more_than_five_rounds(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "heal-report.json").read_text(encoding="utf-8"))
        report["maxRounds"] = 6
        errors = validate_report(report)
        self.assertTrue(any("maxRounds" in error for error in errors))

    def test_round_requires_one_optimization_phase(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "heal-report.json").read_text(encoding="utf-8"))
        report["rounds"][0]["optimizationRunCount"] = 2
        errors = validate_report(report)
        self.assertTrue(any("optimizationRunCount" in error for error in errors))

    def test_nested_heal_cannot_bypass_the_round_protocol(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "heal-report.json").read_text(encoding="utf-8"))
        report["rounds"][0]["repairActions"] = [{"owner": "heal", "operation": "nested"}]
        errors = validate_report(report)
        self.assertTrue(any("recursively" in error for error in errors))

    def test_exam_driven_rejects_six_rounds(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-driven-report.json").read_text(encoding="utf-8"))
        report["maxRounds"] = 6
        errors = validate_exam_driven_report(report)
        self.assertTrue(any("maxRounds" in error for error in errors))

    def test_exam_driven_requires_non_consuming_checks(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-driven-report.json").read_text(encoding="utf-8"))
        report["rounds"][0]["checkBefore"]["consumesRound"] = True
        errors = validate_exam_driven_report(report)
        self.assertTrue(any("consumesRound" in error for error in errors))

    def test_exam_driven_stops_at_round_five(self) -> None:
        metrics = {"readableQuestions": 5, "coveredQuestions": 1, "mappedQuestions": 1, "completeSolutions": 1, "formulaComplete": 1, "sourceComplete": 1, "retrievalSuccess": 1, "unresolvedQuestions": 4}
        rounds = [{"reEvaluation": metrics, "regressions": [], "blockedItems": [], "optimizationStability": {"oscillationDetected": False}} for _ in range(5)]
        self.assertEqual(choose_stop(rounds, 5)[0], "MAX_ROUNDS_REACHED")

    def test_exam_driven_stops_on_optimization_oscillation(self) -> None:
        metrics = {"readableQuestions": 5, "coveredQuestions": 1, "mappedQuestions": 1, "completeSolutions": 1, "formulaComplete": 1, "sourceComplete": 1, "retrievalSuccess": 1, "unresolvedQuestions": 4}
        rounds = [
            {"reEvaluation": metrics, "regressions": [], "blockedItems": [], "optimizationStability": {"oscillationDetected": False}, "optimizationActions": [{"operation": "merge", "targetIds": ["card:a", "card:b"], "newEvidenceRefs": []}]},
            {"reEvaluation": metrics, "regressions": [], "blockedItems": [], "optimizationStability": {"oscillationDetected": False}, "optimizationActions": [{"operation": "split", "targetIds": ["card:a", "card:b"], "newEvidenceRefs": []}]}
        ]
        self.assertEqual(choose_stop(rounds, 5)[0], "STOP_OPTIMIZATION_OSCILLATION")

    def test_exam_driven_consumes_question_by_question_hit_baseline(self) -> None:
        example = json.loads((SKILL_ROOT / "examples" / "exam-driven-report.json").read_text(encoding="utf-8"))
        data = {
            "schemaVersion": "heal.exam-driven.input.v1",
            "healRunId": "heal-hit-integration-001",
            "subjectId": example["subjectId"],
            "examPdfPath": "exam/questions.pdf",
            "ocrUsed": False,
            "delegatedOcr": False,
            "baseline": example["baseline"],
            "examHit": example["examHitBaseline"],
            "split": example["split"],
            "rounds": example["rounds"],
            "maxRounds": 5,
            "readOnlyChecks": example["readOnlyChecks"],
            "webResearch": example["webResearch"],
            "externalSupplements": example["externalSupplements"]
        }
        report = build_exam_driven_report(data)
        self.assertEqual(report["examHitBaseline"]["selectionPolicy"], "all_questions")
        self.assertEqual(report["rounds"][0]["examHitAfter"]["counts"]["HIT"], 2)

    def test_reset_script_targets_only_heal_current(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / ".heal" / "current"
            root.mkdir(parents=True)
            (root / "old-report.json").write_text("old", encoding="utf-8")
            target = validate_target(str(root))
            reset_workspace(target, True)
            self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
