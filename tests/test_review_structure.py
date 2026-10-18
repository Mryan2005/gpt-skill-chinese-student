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

from validate_review_report import validate_report  # noqa: E402


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class ReviewStructureTests(unittest.TestCase):
    def test_front_door_and_contract_exist(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 90)
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "review-contract.md").is_file())

    def test_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "references").glob("*.md"))
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


if __name__ == "__main__":
    unittest.main()
