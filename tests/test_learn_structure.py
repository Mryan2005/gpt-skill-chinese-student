from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "learn"

PLAYBOOKS = {
    "ingest-material.md",
    "learn-topic.md",
    "organize-questions.md",
    "update-existing-subject.md",
    "repair-knowledge-base.md",
    "validate-readiness.md",
}

REFERENCES = {
    "common.md",
    "source-model.md",
    "knowledge-model.md",
    "question-model.md",
    "provenance.md",
    "agent-contract.md",
}


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class LearnStructureTests(unittest.TestCase):
    def test_front_door_is_small_and_routes_every_playbook(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 80)
        for name in PLAYBOOKS:
            self.assertTrue((SKILL_ROOT / "playbooks" / name).is_file(), name)

    def test_platform_references_exist(self) -> None:
        for name in REFERENCES:
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)

    def test_entrypoint_and_playbook_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "playbooks").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_old_workflow_files_are_not_routing_targets(self) -> None:
        entrypoint = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for old_name in ("learning.md", "learning-agents.md"):
            self.assertNotIn(old_name, entrypoint)


if __name__ == "__main__":
    unittest.main()
