from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "review"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "plugin" / "scripts"))

from apply_review_update import apply_review_mastery, apply_review_observations  # noqa: E402
from validate_learner_model import validate_observation  # noqa: E402
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
