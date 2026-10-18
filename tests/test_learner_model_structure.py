from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = REPO_ROOT / "plugin" / "examples" / "learner"
sys.path.insert(0, str(REPO_ROOT / "plugin" / "scripts"))

from validate_learner_model import (  # noqa: E402
    validate_error_model,
    validate_explanation_model,
    validate_mastery,
    validate_observation,
    validate_question_mastery,
    validate_self_report,
    validate_self_report_correction,
    validate_sort_state,
    validate_strategy_state,
)


def load(name: str) -> dict:
    return json.loads((EXAMPLE_ROOT / name).read_text(encoding="utf-8"))


class LearnerModelTests(unittest.TestCase):
    def test_examples_pass(self) -> None:
        self.assertEqual(validate_observation(load("observation.json")), [])
        self.assertEqual(validate_self_report(load("self-report.json")), [])
        self.assertEqual(validate_self_report_correction(load("self-report-correction.json")), [])
        self.assertEqual(validate_error_model(load("error-model.json")), [])
        self.assertEqual(validate_explanation_model(load("explanation-model.json")), [])
        self.assertEqual(validate_mastery(load("mastery.json")), [])
        self.assertEqual(validate_question_mastery(load("question-mastery.json")), [])
        self.assertEqual(validate_strategy_state(load("strategy-state.json")), [])
        self.assertEqual(validate_sort_state(load("sort-state.json")), [])

    def test_personality_inference_is_rejected(self) -> None:
        observation = copy.deepcopy(load("observation.json"))
        observation["learningStyle"] = "visual"
        errors = validate_observation(observation)
        self.assertTrue(any("forbidden inference" in error for error in errors))

    def test_self_report_has_no_ai_confidence_or_inference(self) -> None:
        report = copy.deepcopy(load("self-report.json"))
        report["claims"][0]["confidence"] = 0.9
        errors = validate_self_report(report)
        self.assertTrue(any("confidence" in error for error in errors))

    def test_self_report_correction_requires_user_provenance(self) -> None:
        correction = copy.deepcopy(load("self-report-correction.json"))
        correction["reportedBy"] = "system"
        errors = validate_self_report_correction(correction)
        self.assertTrue(any("reportedBy must be user" in error for error in errors))

    def test_single_error_does_not_create_confident_pattern(self) -> None:
        model = copy.deepcopy(load("error-model.json"))
        model["patterns"][0]["count"] = 1
        model["patterns"][0]["recentCount"] = 1
        model["patterns"][0]["confidence"] = 1.0
        errors = validate_error_model(model)
        self.assertTrue(any("too high for one observation" in error for error in errors))

    def test_question_mastery_verified_requires_independent_evidence(self) -> None:
        mastery = copy.deepcopy(load("question-mastery.json"))
        mastery["questions"]["series-mcq-17"]["status"] = "verified"
        errors = validate_question_mastery(mastery)
        self.assertTrue(any("independent evidence" in error for error in errors))

    def test_sort_state_requires_reason_and_evidence(self) -> None:
        state = copy.deepcopy(load("sort-state.json"))
        state["ranking"][0]["reasons"] = []
        errors = validate_sort_state(state)
        self.assertTrue(any("reasons" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
