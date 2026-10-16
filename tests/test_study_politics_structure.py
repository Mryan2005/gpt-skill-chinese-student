from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "study-politics"


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class StudyPoliticsStructureTests(unittest.TestCase):
    def test_domain_skill_is_small_and_has_contracts(self) -> None:
        self.assertLessEqual(len((SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines()), 80)
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "politics-cards.md").is_file())
        self.assertTrue((SKILL_ROOT / "references" / "politics-integrity.md").is_file())

    def test_links_resolve(self) -> None:
        for document in [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "references").glob("*.md")):
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_card_types_include_political_semantics(self) -> None:
        text = (SKILL_ROOT / "references" / "politics-cards.md").read_text(encoding="utf-8")
        for card_type in ("concept", "principle", "canonical-expression", "comparison", "confusion"):
            self.assertIn(card_type, text)


if __name__ == "__main__":
    unittest.main()
