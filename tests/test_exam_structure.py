from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "exam"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_exam_record import validate_record  # noqa: E402


PLAYBOOKS = {
    "run-exam.md",
    "grade-exam.md",
    "analyze-errors.md",
    "replay-errors.md",
}

REFERENCES = {
    "common.md",
    "exam-contract.md",
    "pdf-reading.md",
    "answer-record.md",
    "grading.md",
    "error-taxonomy.md",
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


if __name__ == "__main__":
    unittest.main()
