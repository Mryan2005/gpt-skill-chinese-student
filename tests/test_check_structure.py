from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "check"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_findings import validate_report  # noqa: E402


PLAYBOOKS = {
    "full-audit.md",
    "source-integrity.md",
    "knowledge-structure.md",
    "question-integrity.md",
    "relation-integrity.md",
    "retrieval-integrity.md",
    "rendering-integrity.md",
    "readiness.md",
}

REFERENCES = {
    "common.md",
    "check-contract.md",
    "finding-schema.md",
    "severity.md",
}


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class CheckStructureTests(unittest.TestCase):
    def test_front_door_is_small_and_routes_every_audit(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 80)
        for name in PLAYBOOKS:
            self.assertTrue((SKILL_ROOT / "playbooks" / name).is_file(), name)

    def test_audit_references_exist(self) -> None:
        for name in REFERENCES:
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)

    def test_entrypoint_and_playbook_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "playbooks").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_finding_report_passes(self) -> None:
        report_path = SKILL_ROOT / "examples" / "finding-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_report(report), [])

    def test_finding_report_rejects_mutation_or_wrong_summary(self) -> None:
        report_path = SKILL_ROOT / "examples" / "finding-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(report)
        mutated["readOnly"] = False
        mutated["summary"]["blocker"] = 0
        errors = validate_report(mutated)
        self.assertTrue(any("readOnly" in error for error in errors))
        self.assertTrue(any("summary.blocker" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
