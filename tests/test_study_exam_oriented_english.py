from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "study-exam-oriented-english"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "plugin" / "skills" / "practice" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "plugin" / "skills" / "optimize" / "scripts"))

from generate_practice_pdfs import generate  # noqa: E402
from plan_optimize import build_report as build_optimize_report  # noqa: E402
from validate_english import validate_record  # noqa: E402
from validate_practice import validate_practice  # noqa: E402


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class StudyExamOrientedEnglishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example = json.loads((SKILL_ROOT / "examples" / "english-record.json").read_text(encoding="utf-8"))

    def test_domain_skill_is_small_and_references_contracts(self) -> None:
        self.assertLessEqual(len((SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines()), 90)
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue((REPO_ROOT / "plugin" / "schemas" / "study-exam-oriented-english" / "english-record.schema.json").is_file())
        for name in ("english-cards.md", "writing.md", "translation.md", "review-contract.md", "integrity.md", "integrations.md"):
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)

    def test_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "references").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_record_and_examples_pass(self) -> None:
        self.assertEqual(validate_record(self.example), [])
        self.assertIn("More and more people depend on the Internet", self.example["writing"]["examples"][0]["recommendedText"])
        self.assertIn("尽管这项政策并不完美", self.example["translation"]["examples"][0]["recommendedTranslation"])

    def test_simplification_cannot_drop_meaning_units(self) -> None:
        record = copy.deepcopy(self.example)
        record["writing"]["examples"][1]["meaningUnitsPreserved"] = ["technology develops quickly"]
        errors = validate_record(record)
        self.assertTrue(any("meaningUnitsPreserved" in error for error in errors))

    def test_correct_simple_sentence_is_not_rewritten(self) -> None:
        record = copy.deepcopy(self.example)
        record["writing"]["examples"][2]["recommendedText"] = "Students ought to organize their schedules effectively."
        errors = validate_record(record)
        self.assertTrue(any("marked unchanged" in error for error in errors))

    def test_translation_preserves_negation_cause_and_comparison(self) -> None:
        record = copy.deepcopy(self.example)
        record["translation"]["examples"][0]["preservedLogicRelations"] = ["concession", "causal"]
        errors = validate_record(record)
        self.assertTrue(any("preservedLogicRelations" in error for error in errors))

    def test_sentence_level_review_diagnosis_is_evidence_backed(self) -> None:
        review = self.example["review"]
        self.assertEqual(review["writingRevisions"][0]["sentenceId"], "user-writing-sentence-001")
        self.assertIn("NEGATION_LOST", review["translationDiagnostics"][0]["errorCodes"])
        self.assertTrue(review["writingRevisions"][1]["preserveIfCorrect"])

    def test_practice_generates_english_writing_and_translation_pdfs(self) -> None:
        input_data = {
            "schemaVersion": "practice-input.v1",
            "subjectId": "english-1",
            "title": "English writing and translation practice",
            "scope": "Simple expression and natural translation",
            "durationMinutes": 45,
            "totalPoints": 10,
            "instructions": ["Write independently; answers are released after submission."],
            "questions": [
                {
                    "questionId": "english-writing-001",
                    "number": 1,
                    "type": "writing",
                    "points": 5,
                    "stem": "Write a short essay about how students should manage time.",
                    "writingRequirements": "State one view, give one reason, and write 100-120 words.",
                    "wordCount": "100-120",
                    "answerSpaceLines": 10,
                    "officialSolution": "A clear paragraph structure with simple, accurate sentences.",
                    "answerStatus": "DERIVED_VERIFIED",
                    "solutionStatus": "DERIVED_COMPLETE",
                    "knowledgeCardIds": ["english-card-reason-001"],
                    "sourceRefs": [{"sourceId": "src-english-writing-001", "locator": "prompt"}]
                },
                {
                    "questionId": "english-translation-001",
                    "number": 2,
                    "type": "translation",
                    "points": 5,
                    "stem": "Translate the following sentence into natural Chinese.",
                    "sourceText": "People often find it difficult to make important decisions when they have too many choices.",
                    "answerSpaceLines": 6,
                    "recommendedTranslation": "选择太多时，人们往往很难做出重要决定。",
                    "keyTerms": "important decisions; too many choices",
                    "logicRelations": "when / condition",
                    "answerStatus": "DERIVED_VERIFIED",
                    "solutionStatus": "DERIVED_COMPLETE",
                    "knowledgeCardIds": ["english-card-logic-translation-001"],
                    "sourceRefs": [{"sourceId": "src-english-translation-002", "locator": "sentence-1"}]
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / ".practice" / "current"
            manifest = generate(input_data, output, "english-practice-test-001")
            record = json.loads((output / "practice-record.json").read_text(encoding="utf-8"))
            self.assertEqual(validate_practice(manifest, record, output / "questions.pdf", output / "answers.pdf"), [])
            self.assertTrue((output / "questions.pdf").stat().st_size > 0)
            self.assertTrue((output / "answers.pdf").stat().st_size > 0)

    def test_integration_contracts_keep_review_and_heal_boundaries(self) -> None:
        integrations = (SKILL_ROOT / "references" / "integrations.md").read_text(encoding="utf-8")
        self.assertIn("review user-written", integrations)
        self.assertIn("heal exam", integrations)
        self.assertIn("External Supplement", integrations)
        self.assertIn("optimize", integrations)

    def test_optimize_keeps_semantically_distinct_expression_cards_separate(self) -> None:
        report = build_optimize_report({
            "optimizeRunId": "english-optimize-test",
            "subjectId": "english-1",
            "cards": [
                {"id": "card:reason", "title": "Give a reason", "body": "Use because to give a reason."},
                {"id": "card:contrast", "title": "Show a contrast", "body": "Use but to show a contrast."}
            ],
            "relatedCandidates": [{"targetIds": ["card:reason", "card:contrast"], "evidenceRefs": ["english:relation"], "reason": "Both are sentence functions but their meanings differ."}]
        }, "sha256:english")
        self.assertFalse(any(operation["type"] in {"exact_duplicate", "semantic_merge", "fragmented_merge"} for operation in report["operations"]))
        self.assertTrue(any(operation["type"] == "related_but_distinct" and operation["decision"] == "NO_OP" for operation in report["operations"]))


if __name__ == "__main__":
    unittest.main()
