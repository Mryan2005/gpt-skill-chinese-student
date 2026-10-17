from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "sort"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_priority import validate_result  # noqa: E402


PLAYBOOKS = {"build-review-priority.md", "tonight-queue.md"}
REFERENCES = {"sort-contract.md", "priority-model.md", "modes.md"}


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


def load_result() -> dict:
    return json.loads((SKILL_ROOT / "examples" / "sort-result.json").read_text(encoding="utf-8"))


class SortStructureTests(unittest.TestCase):
    def test_front_door_is_small_and_routes_playbooks(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 80)
        for name in PLAYBOOKS:
            self.assertTrue((SKILL_ROOT / "playbooks" / name).is_file(), name)
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())

    def test_references_exist(self) -> None:
        for name in REFERENCES:
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)

    def test_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"]
        documents += sorted((SKILL_ROOT / "playbooks").glob("*.md"))
        documents += sorted((SKILL_ROOT / "references").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_priority_result_passes(self) -> None:
        self.assertEqual(validate_result(load_result()), [])

    def test_priority_result_rejects_canonical_mutation(self) -> None:
        result = copy.deepcopy(load_result())
        result["canonicalStructurePreserved"]["contentMutated"] = True
        errors = validate_result(result)
        self.assertTrue(any("canonicalStructurePreserved" in error for error in errors))

    def test_priority_result_rejects_unexplained_score(self) -> None:
        result = copy.deepcopy(load_result())
        result["queue"][0]["priority"]["score"] = 1
        errors = validate_result(result)
        self.assertTrue(any("weighted dimensions" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
