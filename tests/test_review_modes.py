from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "review"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from route_review import route_review  # noqa: E402
from validate_review_mode import validate_review_input  # noqa: E402


class ReviewModeTests(unittest.TestCase):
    def test_exam_result_is_default_material_only_route(self) -> None:
        exam = json.loads((REPO_ROOT / "plugin" / "skills" / "exam" / "examples" / "exam-record.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            exam_path = Path(directory) / "exam-result.json"
            exam_path.write_text(json.dumps(exam), encoding="utf-8")
            manifest = route_review(None, exam_result=exam_path, questions_pdf=None, answers_pdf=None, submission_pdf=None, attempt_id=None, review_run_id="review-exam-001")
        self.assertEqual(manifest["reviewMode"], "exam-result")
        self.assertFalse(manifest["learnerModelWriteAllowed"])
        self.assertFalse(manifest["outputPolicy"]["generatesPdf"])
        self.assertEqual(validate_review_input(manifest), [])

    def test_user_written_requires_new_attempt_and_three_original_pdfs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for name in ("questions.pdf", "answers.pdf", "user-submission.pdf"):
                path = root / name
                path.write_bytes(b"%PDF-demo")
                paths.append(path)
            manifest = route_review("user-written", exam_result=None, questions_pdf=paths[0], answers_pdf=paths[1], submission_pdf=paths[2], attempt_id="practice-001|attempt-1", review_run_id="review-user-001")
        self.assertEqual(manifest["reviewMode"], "user-written")
        self.assertTrue(manifest["learnerModelWriteAllowed"])
        self.assertEqual(validate_review_input(manifest), [])


if __name__ == "__main__":
    unittest.main()
