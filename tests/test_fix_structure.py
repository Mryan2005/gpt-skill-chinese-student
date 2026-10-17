from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "fix"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from compare_findings import compare_findings  # noqa: E402
from validate_fix_report import validate_report  # noqa: E402
from verify_report_version import verify_report  # noqa: E402


PLAYBOOKS = {
    "fix-from-report.md",
    "schema-fix.md",
    "provenance-fix.md",
    "question-fix.md",
    "solution-fix.md",
    "relation-fix.md",
    "latex-fix.md",
    "runtime-fix.md",
    "learner-state-fix.md",
}
REFERENCES = {
    "fix-contract.md",
    "repair-plan-schema.md",
    "patch-proposal-schema.md",
    "conflict-policy.md",
}
AGENTS = {
    "schema-fixer.md",
    "provenance-fixer.md",
    "question-fixer.md",
    "solution-fixer.md",
    "relation-fixer.md",
    "latex-fixer.md",
    "runtime-fixer.md",
    "learner-state-fixer.md",
}


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


def load_report() -> dict:
    return json.loads((SKILL_ROOT / "examples" / "fix-report.json").read_text(encoding="utf-8"))


class FixStructureTests(unittest.TestCase):
    def test_front_door_is_small_and_routes_playbooks(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 80)
        for name in PLAYBOOKS:
            self.assertTrue((SKILL_ROOT / "playbooks" / name).is_file(), name)
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())

    def test_references_and_agents_exist(self) -> None:
        for name in REFERENCES:
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)
        for name in AGENTS:
            self.assertTrue((SKILL_ROOT / "agents" / name).is_file(), name)

    def test_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"]
        documents += sorted((SKILL_ROOT / "playbooks").glob("*.md"))
        documents += sorted((SKILL_ROOT / "references").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_fix_report_passes(self) -> None:
        self.assertEqual(validate_report(load_report()), [])

    def test_fix_report_rejects_source_mutation(self) -> None:
        report = copy.deepcopy(load_report())
        report["sourceMutation"] = True
        errors = validate_report(report)
        self.assertTrue(any("sourceMutation" in error for error in errors))

    def test_stale_check_report_is_rejected(self) -> None:
        check_report = {
            "schemaVersion": "check.finding.v1",
            "artifact": {"version": "v1", "hash": "sha256:old"},
        }
        errors = verify_report(check_report, artifact_version="v1", artifact_hash="sha256:new")
        self.assertTrue(any("STALE_CHECK_REPORT" in error for error in errors))

    def test_no_progress_is_detected_by_fingerprint(self) -> None:
        findings = [{"code": "A", "entityId": "x", "rootLayer": "one"}]
        comparison = compare_findings({"findings": findings}, {"findings": findings})
        self.assertTrue(comparison["noProgress"])
        self.assertFalse(comparison["reduced"])


if __name__ == "__main__":
    unittest.main()
