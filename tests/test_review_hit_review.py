from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = REPO_ROOT / "plugin" / "skills" / "review"
EXAM_ROOT = REPO_ROOT / "plugin" / "skills" / "exam"
sys.path.insert(0, str(REVIEW_ROOT / "scripts"))

from compose_hit_review import compose_hit_review  # noqa: E402
from validate_hit_review import validate_hit_review  # noqa: E402
from validate_annotations import validate_overlay  # noqa: E402
from validate_material_review import validate_material_review  # noqa: E402


class ReviewHitReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hit = json.loads((EXAM_ROOT / "examples" / "exam-hit-report.json").read_text(encoding="utf-8"))
        cls.catalog = json.loads((EXAM_ROOT / "examples" / "exam-hit-input.json").read_text(encoding="utf-8"))

    def test_hit_review_detects_gaps_and_content_anchors(self) -> None:
        report = compose_hit_review(self.hit, review_run_id="review-hit-001", subject_id="math-1", catalog=self.catalog)
        self.assertEqual(validate_hit_review(report), [])
        self.assertTrue(report["gaps"])
        self.assertTrue(report["highlights"])
        self.assertEqual(report["research"]["status"], "PENDING")
        self.assertTrue(all(item["contentAnchor"]["field"] not in {"title", "id"} for item in report["highlights"]))
        self.assertEqual(validate_overlay(report["annotationOverlay"]), [])
        self.assertIn("<mark>", report["studyGuideHtml"])

    def test_research_supplement_is_separate_and_creates_learn_handoff(self) -> None:
        initial = compose_hit_review(self.hit, review_run_id="review-hit-002", subject_id="math-1", catalog=self.catalog)
        gap = next(item for item in initial["gaps"] if item["gapType"] == "content_incomplete")
        supplements = [{
            "supplementId": "supplement-cache-001",
            "sourceUrl": "https://example.edu/cache-method",
            "sourceTitle": "Cache mapping lecture notes",
            "publisher": "Example University",
            "accessedAt": "2026-10-19T12:00:00+08:00",
            "provenanceType": "external_supplement",
            "evidenceStatus": "supported",
            "relatedGapIds": [gap["gapId"]],
            "relatedQuestionIds": gap["questionIds"],
            "relatedCardIds": gap["cardIds"],
            "supportedClaims": ["The missing operation must be recorded with its applicability condition."]
        }]
        report = compose_hit_review(self.hit, review_run_id="review-hit-003", subject_id="math-1", catalog=self.catalog, supplements=supplements)
        self.assertEqual(validate_hit_review(report), [])
        self.assertEqual(report["research"]["status"], "PARTIAL")
        self.assertTrue(any(item["status"] == "ready" for item in report["learnHandoffs"]))
        self.assertIn("example.edu", report["studyGuideHtml"])
        self.assertFalse(report["learnerModelMutation"])

    def test_recheck_separates_original_and_enriched_coverage(self) -> None:
        after = copy.deepcopy(self.hit)
        q2 = next(item for item in after["questionResults"] if item["questionId"] == "math-hit-q2")
        q2["hitResult"]["hitStatus"] = "HIT"
        q2["hitResult"]["missingKnowledge"] = []
        q2["hitResult"]["supportedReasoning"] = "The enriched card now contains the condition and region setup procedure."
        report = compose_hit_review(self.hit, review_run_id="review-hit-004", subject_id="math-1", catalog=self.catalog, hit_after=after, catalog_after=self.catalog)
        self.assertEqual(validate_hit_review(report), [])
        self.assertIn("math-hit-q2", report["comparison"]["improvedQuestionIds"])
        stages = {item["coverageStage"] for item in report["highlights"]}
        self.assertIn("original_exam_hit", stages)
        self.assertIn("enriched_exam_coverage", stages)

    def test_unreliable_external_source_does_not_close_gap(self) -> None:
        initial = compose_hit_review(self.hit, review_run_id="review-hit-006", subject_id="math-1", catalog=self.catalog)
        gap = initial["gaps"][0]
        report = compose_hit_review(self.hit, review_run_id="review-hit-007", subject_id="math-1", catalog=self.catalog, supplements=[{
            "supplementId": "supplement-unreliable",
            "sourceUrl": "https://example.invalid/result",
            "sourceTitle": "Unverified answer page",
            "publisher": "Unknown",
            "accessedAt": "2026-10-19T12:00:00+08:00",
            "provenanceType": "external_supplement",
            "evidenceStatus": "rejected",
            "relatedGapIds": [gap["gapId"]],
            "supportedClaims": ["unverified claim"]
        }])
        self.assertEqual(validate_hit_review(report), [])
        self.assertEqual(report["research"]["status"], "PARTIAL")
        self.assertTrue(report["research"]["unresolvedGapIds"])

    def test_repeated_review_deduplicates_same_content_anchor(self) -> None:
        report = compose_hit_review(self.hit, review_run_id="review-hit-005", subject_id="math-1", catalog=self.catalog)
        keys = [(item["targetId"], item["contentAnchor"]["field"], item["contentAnchor"]["excerpt"], item["coverageStage"]) for item in report["highlights"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_standard_material_review_cli_wires_hit_enrichment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "review"
            result = subprocess.run([
                sys.executable,
                str(REVIEW_ROOT / "scripts" / "material_review.py"),
                "--review-report", str(REVIEW_ROOT / "examples" / "review-report.json"),
                "--exam-hit-before", str(EXAM_ROOT / "examples" / "exam-hit-report.json"),
                "--catalog", str(EXAM_ROOT / "examples" / "exam-hit-input.json"),
                "--output-dir", str(output),
                "--review-run-id", "review-hit-cli-001"
            ], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output / "material-review-report.v2.json").read_text(encoding="utf-8"))
            self.assertIn("examHitReview", report)
            self.assertEqual(validate_material_review(report), [])
            self.assertTrue((output / "hit-review.html").is_file())

    def test_review_consumes_exam_record_hit_without_recomputing_exam(self) -> None:
        exam_record = json.loads((EXAM_ROOT / "examples" / "exam-record.json").read_text(encoding="utf-8"))
        report = compose_hit_review(exam_record, review_run_id="review-exam-record-hit-001", subject_id="math-1", catalog=self.catalog)
        self.assertEqual(validate_hit_review(report), [])
        self.assertEqual(report["hitBefore"]["runId"], exam_record["examId"])
        self.assertEqual(report["comparison"]["status"], "NOT_RECHECKED")


if __name__ == "__main__":
    unittest.main()
