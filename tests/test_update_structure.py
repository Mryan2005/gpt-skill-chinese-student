from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "update"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_migration_plan import validate_plan  # noqa: E402


PLAYBOOKS = {
    "detect.md",
    "plan.md",
    "migrate.md",
    "rebuild.md",
    "validate.md",
    "report.md",
}

REFERENCES = {
    "update-contract.md",
    "migration-plan.md",
    "change-impact.md",
}


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


def load_plan() -> dict:
    return json.loads((SKILL_ROOT / "examples" / "migration-plan.json").read_text(encoding="utf-8"))


class UpdateStructureTests(unittest.TestCase):
    def test_front_door_is_small_and_routes_every_playbook(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 80)
        for name in PLAYBOOKS:
            self.assertTrue((SKILL_ROOT / "playbooks" / name).is_file(), name)

    def test_references_and_migrations_exist(self) -> None:
        for name in REFERENCES:
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)
        self.assertTrue((SKILL_ROOT / "migrations" / "001-source-derived-separation.md").is_file())
        self.assertTrue((REPO_ROOT / "plugin/skills/study-math/migrations/001-typed-relations.md").is_file())
        self.assertTrue((REPO_ROOT / "plugin/skills/study-politics/migrations/001-source-derived-politics.md").is_file())

    def test_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "playbooks").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_plan_passes(self) -> None:
        self.assertEqual(validate_plan(load_plan()), [])

    def test_non_idempotent_or_source_mutating_step_fails(self) -> None:
        plan = copy.deepcopy(load_plan())
        plan["steps"][0]["idempotent"] = False
        plan["steps"][1]["sourceMutation"] = "allowed"
        errors = validate_plan(plan)
        self.assertTrue(any("idempotent" in error for error in errors))
        self.assertTrue(any("sourceMutation" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
