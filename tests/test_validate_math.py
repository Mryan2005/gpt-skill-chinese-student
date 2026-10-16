from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "plugin" / "skills" / "study-math" / "scripts"))

from validate_math import validate_record  # noqa: E402


EXAMPLE = REPO_ROOT / "plugin" / "skills" / "study-math" / "examples" / "math-records.json"


def load_example() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def issue_codes(record: dict) -> set[str]:
    return {issue.code for issue in validate_record(record).issues}


class StudyMathValidatorTests(unittest.TestCase):
    def test_reference_record_is_exam_ready(self) -> None:
        report = validate_record(load_example())
        self.assertTrue(report.passed, report.issues)
        self.assertEqual(report.metrics["atomic_card_rate"], 1.0)
        self.assertEqual(report.metrics["question_primary_mapping_rate"], 1.0)
        self.assertEqual(report.metrics["metadata_leakage_rate"], 0.0)

    def test_case_a_chapter_overview_cannot_be_a_question(self) -> None:
        record = load_example()
        question = record["questions"][0]
        question["sourceId"] = "series-overview"
        question["sourceIds"] = ["series-overview"]
        codes = issue_codes(record)
        self.assertIn("META_AS_QUESTION", codes)
        self.assertIn("SOURCE_METADATA_IN_QUESTION_BANK", codes)

    def test_unclassified_source_cannot_pass_readiness(self) -> None:
        record = load_example()
        record["sources"].append(
            {
                "id": "unclassified-photo",
                "entityType": "unclassified",
                "title": "待分类照片",
                "status": "COMPLETE",
                "provenance": {"kind": "原始材料"},
                "mathObjects": [],
            }
        )
        codes = issue_codes(record)
        self.assertIn("SOURCE_UNCLASSIFIED", codes)

    def test_case_b_lost_formula_is_not_complete(self) -> None:
        record = load_example()
        source = next(source for source in record["sources"] if source["id"] == "series-q12")
        math_object = source["mathObjects"][0]
        math_object["status"] = "LOST"
        codes = issue_codes(record)
        self.assertIn("MATH_CONTENT_LOSS", codes)

    def test_case_c_historical_answer_stays_unverified(self) -> None:
        record = load_example()
        question = record["questions"][0]
        question["officialAnswer"] = None
        question["derivedAnswer"] = None
        question["historicalAnswer"] = "B"
        question["answerEvidence"] = [
            {"kind": "historical_answer", "value": "B", "sourceId": "series-q12-answer"}
        ]
        question["answerStatus"] = "ANSWER_UNVERIFIED"
        codes = issue_codes(record)
        self.assertIn("ANSWER_UNVERIFIED", codes)
        self.assertNotIn("QUESTION_ANSWER_MISMATCH", codes)

    def test_missing_answer_blocks_exam_readiness(self) -> None:
        record = load_example()
        question = record["questions"][0]
        question["officialAnswer"] = None
        question["historicalAnswer"] = None
        question["derivedAnswer"] = None
        question["answerEvidence"] = []
        question["answerStatus"] = "ANSWER_MISSING"
        codes = issue_codes(record)
        self.assertIn("ANSWER_MISSING", codes)

    def test_source_status_is_independent_and_blocks_readiness(self) -> None:
        record = load_example()
        record["questions"][0]["sourceStatus"] = "CONFLICTING"
        codes = issue_codes(record)
        self.assertIn("SOURCE_INCOMPLETE", codes)

    def test_question_and_solution_statuses_are_independent(self) -> None:
        record = load_example()
        question = record["questions"][0]
        question["solution"] = {
            "status": "SOLUTION_INCOMPLETE",
            "verifiedFragment": "只读到相邻项比值的第一步。",
        }
        question["solutionStatus"] = "SOLUTION_INCOMPLETE"
        codes = issue_codes(record)
        self.assertIn("SOLUTION_INCOMPLETE", codes)
        self.assertNotIn("QUESTION_INCOMPLETE", codes)

    def test_case_d_expected_question_identity_cannot_be_replaced_by_metadata(self) -> None:
        record = load_example()
        source = next(source for source in record["sources"] if source["id"] == "series-q12")
        source["expectedQuestions"] = [
            {"number": 49, "type": "multiple_choice"},
            {"number": 21, "type": "proof"},
        ]
        codes = issue_codes(record)
        self.assertIn("QUESTION_IDENTITY_MISMATCH", codes)

    def test_case_e_solution_semantics_must_match_stem(self) -> None:
        record = load_example()
        record["questions"][0]["semanticProfile"]["solutionConcepts"] = ["sin", "tan"]
        codes = issue_codes(record)
        self.assertIn("QUESTION_SOLUTION_MISMATCH", codes)

    def test_case_f_primary_card_follows_real_operation(self) -> None:
        record = load_example()
        record["questions"][0]["primaryCardId"] = "limit-tools-comparison"
        codes = issue_codes(record)
        self.assertIn("QUESTION_CARD_MISMATCH", codes)

    def test_case_g_broad_card_must_be_split(self) -> None:
        record = load_example()
        ratio_card = next(card for card in record["cards"] if card["id"] == "ratio-test")
        ratio_card["scopeConcepts"] = ["单调", "极值", "凹凸", "拐点"]
        codes = issue_codes(record)
        self.assertIn("CARD_TOO_BROAD", codes)

    def test_case_h_bridge_without_outgoing_relation_fails(self) -> None:
        record = load_example()
        bridge = next(card for card in record["cards"] if card["id"] == "series-test-bridge")
        bridge["outgoingRelationIds"] = []
        bridge["relationIds"] = []
        codes = issue_codes(record)
        self.assertIn("EMPTY_BRIDGE", codes)

    def test_duplicate_question_is_reported_without_deleting_either_record(self) -> None:
        record = load_example()
        duplicate = copy.deepcopy(record["questions"][0])
        duplicate["id"] = "series-mcq-12-copy"
        record["questions"].append(duplicate)
        codes = issue_codes(record)
        self.assertIn("QUESTION_DUPLICATED", codes)
        self.assertEqual(len(record["questions"]), 2)


if __name__ == "__main__":
    unittest.main()
