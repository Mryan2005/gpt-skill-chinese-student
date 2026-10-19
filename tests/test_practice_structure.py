from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "practice"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from generate_practice_pdfs import generate  # noqa: E402
from validate_practice import validate_practice  # noqa: E402


class PracticeStructureTests(unittest.TestCase):
    def test_skill_and_contract_exist(self) -> None:
        self.assertTrue((SKILL_ROOT / "SKILL.md").is_file())
        self.assertTrue((SKILL_ROOT / "playbooks" / "generate-pdf.md").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "practice-contract.md").is_file())
        self.assertTrue((SKILL_ROOT / "scripts" / "generate_practice_pdfs.py").is_file())

    def test_example_generates_separate_pdfs_and_record(self) -> None:
        input_data = json.loads((SKILL_ROOT / "examples" / "practice-input.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / ".practice" / "current"
            manifest = generate(input_data, output, "practice-test-001")
            record = json.loads((output / "practice-record.json").read_text(encoding="utf-8"))
            errors = validate_practice(manifest, record, output / "questions.pdf", output / "answers.pdf")
            self.assertEqual(errors, [])
            self.assertTrue((output / "questions.pdf").is_file())
            self.assertTrue((output / "answers.pdf").is_file())
            self.assertNotEqual((output / "questions.pdf").read_bytes(), (output / "answers.pdf").read_bytes())

    def test_new_run_archives_previous_current(self) -> None:
        input_data = json.loads((SKILL_ROOT / "examples" / "practice-input.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / ".practice" / "current"
            generate(input_data, output, "practice-test-001")
            generate(copy.deepcopy(input_data), output, "practice-test-002")
            history = output.parent / "history"
            self.assertTrue(any(history.iterdir()))
            self.assertTrue((output / "practice-record.json").is_file())


if __name__ == "__main__":
    unittest.main()
