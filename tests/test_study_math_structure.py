from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "study-math"

PLAYBOOKS = {
    "ingest-material.md",
    "learn-topic.md",
    "organize-question-set.md",
    "build-cards.md",
    "update-subject.md",
    "repair-knowledge-map.md",
    "validate-exam-readiness.md",
}

REFERENCES = {
    "principles.md",
    "card-schema.md",
    "question-schema.md",
    "relation-schema.md",
    "source-schema.md",
    "math-integrity.md",
    "math-rendering.md",
    "math-agents.md",
}


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class StudyMathStructureTests(unittest.TestCase):
    def test_front_door_is_small_and_routes_every_playbook(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 80)
        for name in PLAYBOOKS:
            self.assertTrue((SKILL_ROOT / "playbooks" / name).is_file(), name)

    def test_contract_references_exist(self) -> None:
        for name in REFERENCES:
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)

    def test_entrypoint_and_playbook_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "playbooks").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_old_schema_names_are_not_routing_targets(self) -> None:
        entrypoint = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for old_name in ("math-cards.md", "math-questions.md", "math-relations.md", "math-knowledge.md"):
            self.assertNotIn(old_name, entrypoint)


if __name__ == "__main__":
    unittest.main()
