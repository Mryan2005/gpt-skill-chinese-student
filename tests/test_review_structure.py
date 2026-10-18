from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "review"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "plugin" / "scripts"))

from apply_review_update import apply_review_mastery, apply_review_observations  # noqa: E402
from material_review import build_material_review  # noqa: E402
from reset_review_workspace import reset_workspace, validate_target  # noqa: E402
from render_annotations import render_markdown  # noqa: E402
from validate_learner_model import validate_observation  # noqa: E402
from validate_annotations import validate_overlay  # noqa: E402
from validate_exam_result import validate_exam_result  # noqa: E402
from validate_material_review import validate_material_review  # noqa: E402
from validate_review_report import validate_report  # noqa: E402


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class ReviewStructureTests(unittest.TestCase):
    def test_front_door_and_contract_exist(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 90)
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "review-contract.md").is_file())
        self.assertTrue((SKILL_ROOT / "playbooks" / "postmortem.md").is_file())
        self.assertTrue((SKILL_ROOT / "scripts" / "reset_review_workspace.py").is_file())
        self.assertTrue((SKILL_ROOT / "scripts" / "validate_exam_result.py").is_file())
        self.assertTrue((SKILL_ROOT / "scripts" / "extract_native_pdf_material.py").is_file())

    def test_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "references").glob("*.md")) + sorted((SKILL_ROOT / "playbooks").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_review_report_passes(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "review-report.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_report(report), [])

    def test_closed_exam_result_input_passes(self) -> None:
        result = json.loads((SKILL_ROOT / "examples" / "exam-result.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_exam_result(result), [])

    def test_annotation_overlay_passes(self) -> None:
        overlay = json.loads((SKILL_ROOT / "examples" / "annotation-overlay.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_overlay(overlay), [])
        rendered = render_markdown(overlay)
        self.assertIn("Review highlights", rendered)
        self.assertIn("ratio-test", rendered)

    def test_agent_material_review_does_not_write_user_model(self) -> None:
        result = json.loads((SKILL_ROOT / "examples" / "exam-result.json").read_text(encoding="utf-8"))
        result["answerer"]["type"] = "agent"
        material = build_material_review(result, "material-review-agent-test")
        self.assertFalse(material["learnerModelWriteAllowed"])
        self.assertEqual(validate_material_review(material), [])
        self.assertTrue(material["annotations"])
        self.assertNotIn("weak", json.dumps(material, ensure_ascii=False))

    def test_material_review_example_passes(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "material-review-report.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_material_review(report), [])

    def test_material_review_is_material_only_even_for_human_input(self) -> None:
        result = json.loads((SKILL_ROOT / "examples" / "exam-result.json").read_text(encoding="utf-8"))
        material = build_material_review(result, "material-review-human-test")
        self.assertEqual(material["answererType"], "human")
        self.assertFalse(material["learnerModelWriteAllowed"])
        self.assertFalse(material["learnerModelMutation"])
        self.assertEqual(material["learnerModel"]["masteryChanges"], 0)

    def test_material_review_uses_real_cards_and_reports_overlap(self) -> None:
        review = {
            "schemaVersion": "review.report.v2",
            "reviewRunId": "review-demo",
            "exam": {"examRunId": "exam-demo", "subjectId": "math-1", "answererType": "agent"},
            "questions": [
                {"questionId": "q1", "observedOutcome": "correct", "artifactStatus": "OK", "answerConflict": False, "knowledgeLinks": {"primaryCardId": "card-a", "secondaryCardIds": [], "mappingStatus": "complete"}, "diagnosis": {"evidenceRefs": ["review:q1"]}},
                {"questionId": "q2", "observedOutcome": "incorrect", "artifactStatus": "ANSWER_PROVENANCE_CONFLICT", "answerConflict": True, "knowledgeLinks": {"primaryCardId": "card-a", "secondaryCardIds": [], "mappingStatus": "complete"}, "diagnosis": {"evidenceRefs": ["review:q2"]}},
                {"questionId": "q3", "observedOutcome": "unanswered", "artifactStatus": "GRAPH_MAPPING_MISSING", "answerConflict": False, "knowledgeLinks": {"primaryCardId": "__unmapped__", "secondaryCardIds": [], "mappingStatus": "blocked"}, "diagnosis": {"evidenceRefs": ["review:q3"]}}
            ]
        }
        catalog = {
            "cards": [{"id": "card-a", "title": "Card A", "group": "demo", "explain": ["A concept."], "boundaries": ["A boundary."], "method": "Check A.", "highlights": ["A statement."], "sourceRefs": [{"sourceId": "source-a", "locator": "p1"}]}],
            "questions": [{"id": "q1", "stem": "What is A?", "options": [["A", "A"]], "answer": ["A"], "officialAnswer": "A", "type": "single_choice"}],
            "relations": []
        }
        first = build_material_review(review, "material-review-demo", catalog=catalog)
        second = build_material_review(review, "material-review-demo", catalog=catalog)
        self.assertEqual(first, second)
        self.assertEqual(first["blockerAnalysis"]["originalBlockerCounts"], {"GRAPH_MAPPING_MISSING": 1, "SOURCE_INCOMPLETE": 0, "ANSWER_PROVENANCE_CONFLICT": 1})
        self.assertEqual(first["blockerAnalysis"]["uniqueAffectedQuestionCount"], 2)
        self.assertEqual(first["blockerAnalysis"]["pairwiseOverlap"][0]["questionCount"], 0)
        self.assertEqual(first["coverage"]["focusCardCount"], 1)
        self.assertEqual(first["coverage"]["questionAnalysisProducedCount"], 1)
        self.assertEqual(len(first["questionAnalyses"]), 1)
        self.assertEqual(first["questionAnalyses"][0]["questionId"], "q1")
        self.assertIn("#card-card-a", first["studyGuideHtml"])
        self.assertTrue(any(item["status"] == "unresolved_anchor" for item in first["annotationOverlay"]["annotations"]))
        self.assertEqual(validate_material_review(first), [])

    def test_report_rejects_exam_or_artifact_mutation(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "review-report.json").read_text(encoding="utf-8"))
        mutated = copy.deepcopy(report)
        mutated["examResultMutation"] = True
        mutated["artifactMutation"] = True
        errors = validate_report(mutated)
        self.assertTrue(any("examResultMutation" in error for error in errors))
        self.assertTrue(any("artifactMutation" in error for error in errors))

    def test_report_rejects_unfrozen_exam(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "review-report.json").read_text(encoding="utf-8"))
        report["exam"]["answersFrozen"] = False
        errors = validate_report(report)
        self.assertTrue(any("answersFrozen" in error for error in errors))

    def test_report_rejects_scope_violation_and_blocked_attribution(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "review-report.json").read_text(encoding="utf-8"))
        report["reviewScope"]["regraded"] = True
        report["questions"][1]["learnerAttributionEligible"] = False
        errors = validate_report(report)
        self.assertTrue(any("REVIEW_SCOPE_VIOLATION" in error for error in errors))
        self.assertTrue(any("LEARNER_UPDATE_FROM_BLOCKED_QUESTION" in error for error in errors))

    def test_non_human_exam_cannot_update_user_learner_model(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "review-report.json").read_text(encoding="utf-8"))
        report["exam"]["answererType"] = "agent"
        errors = validate_report(report)
        self.assertTrue(any("LEARNER_UPDATE_FROM_NON_HUMAN" in error for error in errors))

    def test_review_workspace_reset_is_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / ".review" / "current"
            root.mkdir(parents=True)
            (root / "review-report.json").write_text("old", encoding="utf-8")
            target = validate_target(str(root))
            reset_workspace(target, True)
            self.assertEqual(list(target.iterdir()), [])

    def test_review_update_is_idempotent(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "review-report.json").read_text(encoding="utf-8"))
        first, added, skipped = apply_review_observations(report, [])
        second, added_again, skipped_again = apply_review_observations(report, first)
        self.assertEqual(added, 1)
        self.assertEqual(skipped, 0)
        self.assertEqual(added_again, 0)
        self.assertEqual(skipped_again, 1)
        self.assertEqual(first, second)
        self.assertEqual(validate_observation(json.loads(first[0])), [])

    def test_mastery_update_is_idempotent_and_separate(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "review-report.json").read_text(encoding="utf-8"))
        cards, questions, added, skipped = apply_review_mastery(report, {"cards": {}}, {"questions": {}})
        cards_again, questions_again, added_again, skipped_again = apply_review_mastery(report, cards, questions)
        self.assertEqual(added, 4)
        self.assertEqual(skipped, 0)
        self.assertEqual(added_again, 0)
        self.assertEqual(skipped_again, 4)
        self.assertEqual(cards, cards_again)
        self.assertEqual(questions, questions_again)
        self.assertIn("reviewAssessments", cards)
        self.assertIn("questions", questions)

    def test_only_learner_outcomes_write_observations(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "review-report.json").read_text(encoding="utf-8"))
        report["questions"][1]["learnerModelUpdate"]["observation"] = False
        lines, added, skipped = apply_review_observations(report, [])
        self.assertEqual(lines, [])
        self.assertEqual(added, 0)
        self.assertEqual(skipped, 0)

    def test_unanswered_is_not_an_error(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "review-report.json").read_text(encoding="utf-8"))
        question = report["questions"][1]
        question["observedOutcome"] = "unanswered"
        question["diagnosis"].update({"errorCategory": "UNKNOWN", "errorStep": None, "diagnosticStatus": "unknown", "confidence": 0, "hypotheses": []})
        question["learnerModelUpdate"] = {"observation": False, "idempotencyKey": question["learnerModelUpdate"]["idempotencyKey"]}
        question["route"] = "none"
        question["knowledgeMastery"][0].update({"newStatus": "unknown", "assessmentReason": "No response provides no mastery evidence."})
        question["questionMastery"].update({"newStatus": "unknown", "assessmentReason": "No response provides no question mastery evidence."})
        report["completeness"]["counts"].update({"attempted": 1, "scored": 1, "unanswered": 1})
        report["completeness"]["diagnosticCompleteness"] = "PARTIAL"
        report["completeness"]["masteryUpdateStatus"] = "PARTIAL"
        report["learnerModel"]["observationsAppended"] = 0
        report["learnerModel"]["idempotencyKeys"] = []
        self.assertEqual(validate_report(report), [])


if __name__ == "__main__":
    unittest.main()
