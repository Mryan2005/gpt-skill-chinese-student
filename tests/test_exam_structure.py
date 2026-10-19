from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "exam"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_exam_record import validate_record  # noqa: E402
from reset_exam_workspace import reset_workspace, validate_target  # noqa: E402
from run_exam_hit_stage import build_report  # noqa: E402
from validate_exam_hit_stage import validate_report as validate_hit_report  # noqa: E402
from build_recovery_tasks import build_tasks  # noqa: E402
from run_recovery import run_recovery  # noqa: E402
from validate_recovery_tasks import validate_tasks  # noqa: E402


PLAYBOOKS = {
    "run-exam.md",
    "grade-exam.md",
    "analyze-errors.md",
    "replay-errors.md",
}

REFERENCES = {
    "common.md",
    "exam-contract.md",
    "exam-workspace.md",
    "pdf-reading.md",
    "answer-record.md",
    "grading.md",
    "error-taxonomy.md",
    "exam-phase-contract.md",
}


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


def load_example() -> dict:
    return json.loads((SKILL_ROOT / "examples" / "exam-record.json").read_text(encoding="utf-8"))


class ExamStructureTests(unittest.TestCase):
    def test_front_door_is_small_and_routes_every_playbook(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 80)
        for name in PLAYBOOKS:
            self.assertTrue((SKILL_ROOT / "playbooks" / name).is_file(), name)

    def test_exam_references_exist(self) -> None:
        for name in REFERENCES:
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)

    def test_entrypoint_and_playbook_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "playbooks").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_closed_example_is_valid(self) -> None:
        self.assertEqual(validate_record(load_example()), [])

    def test_exam_hit_example_is_valid_and_covers_every_question(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-phase-hit-report.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_hit_report(report), [])
        self.assertEqual(report["coverageSummary"]["totalQuestions"], len(report["questionResults"]))
        self.assertTrue(report["generatedFromAllQuestions"])

    def test_exam_hit_is_content_based_not_title_based(self) -> None:
        data = json.loads((SKILL_ROOT / "examples" / "exam-phase-hit-input.json").read_text(encoding="utf-8"))
        data["questions"][0]["hitResult"]["supportingCardContentRefs"][0]["field"] = "title"
        with self.assertRaises(ValueError):
            build_report(data)

    def test_exam_hit_missing_mapping_can_still_be_hit(self) -> None:
        data = json.loads((SKILL_ROOT / "examples" / "exam-phase-hit-input.json").read_text(encoding="utf-8"))
        result = build_report(data)
        first = next(item for item in result["questionResults"] if item["questionId"] == "math-hit-q1")
        self.assertEqual(first["hitResult"]["hitStatus"], "HIT")
        self.assertIn("direct_mapping_missing", first["hitResult"]["mappingIssues"])

    def test_exam_hit_does_not_turn_unreadable_into_miss(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-phase-hit-report.json").read_text(encoding="utf-8"))
        statuses = {item["questionId"]: item["hitResult"]["hitStatus"] for item in report["questionResults"]}
        self.assertEqual(statuses["math-hit-q4"], "UNRESOLVED")
        self.assertEqual(report["coverageSummary"]["counts"]["MISS"], 0)

    def test_exam_hit_requires_a_failure_reason_for_unresolved(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-phase-hit-report.json").read_text(encoding="utf-8"))
        report["questionResults"][-1]["hitResult"].pop("failureReason")
        errors = validate_hit_report(report)
        self.assertTrue(any("failureReason is required" in error for error in errors))

    def test_recovery_tasks_keep_one_task_per_non_hit_question(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-phase-hit-report.json").read_text(encoding="utf-8"))
        tasks = build_tasks(report)
        self.assertEqual(len(tasks["tasks"]), 2)
        self.assertEqual({item["questionId"] for item in tasks["tasks"]}, {"math-hit-q2", "math-hit-q4"})
        self.assertIn(tasks["tasks"][-1]["failureReason"], {"question_unreadable", "question_boundary_missing"})

    def test_recovery_runner_resumes_and_preserves_original_hit(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-phase-hit-report.json").read_text(encoding="utf-8"))
        ledger = build_tasks(report)
        attempt = {
            "attemptId": "recovery-math-hit-q4-001",
            "questionId": "math-hit-q4",
            "action": "source_recovery",
            "status": "RECOVERED",
            "attemptedAt": "2026-10-19T13:00:00+08:00",
            "method": "native_pdf_visual_recheck",
            "ocrUsed": False,
            "delegatedOcr": False,
            "intermediateTextSources": [],
            "evidenceRefs": ["original_pdf:exam/questions.pdf:page-3"],
            "result": {
                "readStatus": "READABLE",
                "hitResult": {
                    "hitStatus": "HIT",
                    "supportingCardIds": ["card:banker"],
                    "supportingCardContentRefs": [{"cardId": "card:banker", "field": "method", "excerpt": "Need = Max − Allocation, repeatedly select a process with Need ≤ Work", "contentSha256": "sha256:banker"}],
                    "supportedReasoning": "Recovered page content makes the algorithm requirement readable.",
                    "missingKnowledge": [],
                    "mappingIssues": [],
                    "evidenceRefs": ["original_pdf:exam/questions.pdf:page-3"],
                    "confidence": 0.82
                }
            }
        }
        first = run_recovery(report, ledger, [attempt])
        self.assertEqual(first["recoveredHit"]["questionResults"][-1]["hitResult"]["hitStatus"], "HIT")
        self.assertFalse(first["examResultMutation"])
        self.assertEqual(validate_tasks(first["ledger"]), [])
        second = run_recovery(report, first["ledger"], [attempt])
        self.assertEqual(second["ledger"]["tasks"], first["ledger"]["tasks"])
        self.assertEqual(second["originalHit"]["coverageSummary"], report["coverageSummary"])

    def test_exam_hit_can_record_a_readable_true_miss(self) -> None:
        data = json.loads((SKILL_ROOT / "examples" / "exam-phase-hit-input.json").read_text(encoding="utf-8"))
        question = data["questions"][1]
        question["hitResult"] = {
            "hitStatus": "MISS",
            "supportingCardIds": [],
            "supportingCardContentRefs": [],
            "supportedReasoning": "The readable question requires a region setup procedure that no frozen card contains.",
            "missingKnowledge": ["region setup procedure"],
            "mappingIssues": ["direct_mapping_missing"],
            "evidenceRefs": ["question:math-hit-q2", "snapshot:math-1-snapshot-001"],
            "confidence": 0.88
        }
        report = build_report(data)
        self.assertEqual(report["coverageSummary"]["counts"]["MISS"], 1)

    def test_exam_hit_does_not_mutate_learner_or_snapshot(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "exam-phase-hit-report.json").read_text(encoding="utf-8"))
        self.assertFalse(report["learnerModelMutation"])
        self.assertFalse(report["snapshotMutated"])
        mutated = copy.deepcopy(report)
        mutated["snapshotMutated"] = True
        self.assertTrue(any("snapshotMutated" in error for error in validate_hit_report(mutated)))

    def test_exam_hit_domain_cases_cover_math_408_politics_and_english(self) -> None:
        base = json.loads((SKILL_ROOT / "examples" / "exam-phase-hit-input.json").read_text(encoding="utf-8"))
        cases = [
            ("math-1", "card:substitution", "method", "transform the differential, change bounds"),
            ("computer-408", "card:cache", "method", "Compute block offset bits, set/index bits"),
            ("politics-1", "card:principle", "coreMeaning", "The principle requires a concrete condition and canonical wording."),
            ("english-1", "card:translation", "method", "Identify the main clause and preserve logic relations.")
        ]
        for subject_id, card_id, field, excerpt in cases:
            data = copy.deepcopy(base)
            data["subjectId"] = subject_id
            data["snapshot"]["subjectId"] = subject_id
            data["cards"] = [{"cardId": card_id, "content": {field: excerpt}, "contentSha256": f"sha256:{subject_id}"}]
            question = data["questions"][0]
            question["questionId"] = f"{subject_id}-q1"
            question["requiredKnowledge"] = [{"requirementId": "r1", "kind": "method", "description": "Use the domain method."}]
            question["hitResult"]["supportingCardIds"] = [card_id]
            question["hitResult"]["supportingCardContentRefs"] = [{"cardId": card_id, "field": field, "excerpt": excerpt, "contentSha256": f"sha256:{subject_id}"}]
            question["hitResult"]["evidenceRefs"] = [f"question:{question['questionId']}", card_id]
            data["questions"] = [question]
            report = build_report(data)
            self.assertEqual(report["coverageSummary"]["counts"]["HIT"], 1, subject_id)

    def test_frozen_answers_cannot_be_mutated(self) -> None:
        record = copy.deepcopy(load_example())
        record["questions"][0]["firstPassFrozen"] = False
        errors = validate_record(record)
        self.assertTrue(any("firstPassFrozen" in error for error in errors))

    def test_ocr_or_surrogate_pdf_input_fails_integrity_gate(self) -> None:
        record = copy.deepcopy(load_example())
        record["pdfReading"]["examPdf"]["ocrUsed"] = True
        record["questions"][0]["examPage"]["path"] = "exam/questions_ocr.txt"
        errors = validate_record(record)
        self.assertTrue(any("PDF_SOURCE_INTEGRITY_GATE" in error for error in errors))

    def test_delegated_ocr_is_transitively_forbidden(self) -> None:
        record = copy.deepcopy(load_example())
        record["pdfReading"]["examPdf"]["delegatedOcr"] = True
        record["accessLog"].append({"phase": "FIRST_PASS", "source": "ocr", "detail": "delegated helper"})
        errors = validate_record(record)
        self.assertTrue(any("PDF_SOURCE_INTEGRITY_GATE" in error for error in errors))

    def test_outdated_subject_cannot_start_frozen_exam(self) -> None:
        record = copy.deepcopy(load_example())
        record["snapshot"]["migrationStatus"] = "MIGRATION_REQUIRED"
        errors = validate_record(record)
        self.assertTrue(any("UPDATE_REQUIRED_BEFORE_EXAM" in error for error in errors))

    def test_update_cannot_mutate_frozen_exam(self) -> None:
        record = copy.deepcopy(load_example())
        record["updateAppliedAfterFreeze"] = True
        errors = validate_record(record)
        self.assertTrue(any("UPDATE_MUTATED_FROZEN_EXAM" in error for error in errors))

    def test_residual_workspace_blocks_exam(self) -> None:
        record = copy.deepcopy(load_example())
        record["workspace"]["residualPaths"] = ["first-pass-answers.json"]
        errors = validate_record(record)
        self.assertTrue(any("EXAM_WORKSPACE_NOT_CLEAN" in error for error in errors))

    def test_independent_answerer_cannot_retrieve_graph_after_hit(self) -> None:
        record = copy.deepcopy(load_example())
        first_pass = record["questions"][0]["firstPass"]
        first_pass["retrieval"]["directMappingAvailable"] = False
        first_pass["retrieval"]["result"] = "FOUND"
        errors = validate_record(record)
        self.assertTrue(any("EXAM_HIT_ISOLATION" in error for error in errors))

    def test_graph_gap_requires_broad_retrieval_and_blocked_grading(self) -> None:
        record = copy.deepcopy(load_example())
        question = record["questions"][1]
        question["firstPass"].update(
            {
                "attemptStatus": "BLOCKED_BY_GRAPH_KNOWLEDGE_GAP",
                "answer": None,
                "reasoningSummary": "已完成冻结图谱检索，但未找到足以支持判断的知识。",
                "retrieval": {
                    "directMappingAvailable": False,
                    "attempted": False,
                    "queries": [],
                    "candidateCardIds": [],
                    "selectedCardIds": [],
                    "result": "NOT_ATTEMPTED",
                    "evidence": []
                }
            }
        )
        question["hit"]["hitStatus"] = "MISS"
        question["hit"]["missingKnowledge"] = ["required method"]
        question["blockerEvidence"] = ["retrieval:broad-search:math-1"]
        question["artifactStatus"] = "GRAPH_KNOWLEDGE_GAP"
        question["grading"] = {"gradingStatus": "BLOCKED", "result": "blocked", "score": 0, "errorTypes": []}
        record["firstPassCoverage"].update({"answered": 1, "blocked": 1})
        self.assertEqual(validate_record(record), [])

    def test_unprocessed_question_cannot_freeze(self) -> None:
        record = copy.deepcopy(load_example())
        record["questions"][1]["firstPass"].pop("attemptStatus")
        errors = validate_record(record)
        self.assertTrue(any("FIRST_PASS_STATUS_MISSING" in error for error in errors))

    def test_answered_empty_answer_is_invalid(self) -> None:
        record = copy.deepcopy(load_example())
        record["questions"][0]["firstPass"]["answer"] = ""
        errors = validate_record(record)
        self.assertTrue(any("FIRST_PASS_ANSWER_MISSING" in error for error in errors))

    def test_reset_script_deletes_only_the_exact_current_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / ".exam" / "current"
            root.mkdir(parents=True)
            (root / "old-answers.json").write_text("old", encoding="utf-8")
            target = validate_target(str(root))
            reset_workspace(target, True)
            self.assertEqual(list(target.iterdir()), [])



if __name__ == "__main__":
    unittest.main()
