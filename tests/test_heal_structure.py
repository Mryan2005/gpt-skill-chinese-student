from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "heal"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from reset_heal_workspace import reset_workspace, validate_target  # noqa: E402
from validate_heal_report import validate_report  # noqa: E402


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class HealStructureTests(unittest.TestCase):
    def test_front_door_and_contract_exist(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 90)
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "heal-contract.md").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "run-state.md").is_file())

    def test_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"]
        documents += sorted((SKILL_ROOT / "references").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_heal_report_passes(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "heal-report.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_report(report), [])

    def test_report_rejects_stale_fix_and_source_mutation(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "heal-report.json").read_text(encoding="utf-8"))
        mutated = copy.deepcopy(report)
        mutated["rounds"][0]["fix"]["artifactHashBefore"] = "sha256:stale"
        mutated["rounds"][0]["fix"]["sourceMutation"] = True
        errors = validate_report(mutated)
        self.assertTrue(any("STALE_CHECK_REPORT" in error for error in errors))
        self.assertTrue(any("sourceMutation" in error for error in errors))

    def test_report_rejects_more_than_ten_rounds(self) -> None:
        report = json.loads((SKILL_ROOT / "examples" / "heal-report.json").read_text(encoding="utf-8"))
        report["maxRounds"] = 11
        errors = validate_report(report)
        self.assertTrue(any("maxRounds" in error for error in errors))

    def test_reset_script_targets_only_heal_current(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / ".heal" / "current"
            root.mkdir(parents=True)
            (root / "old-report.json").write_text("old", encoding="utf-8")
            target = validate_target(str(root))
            reset_workspace(target, True)
            self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
