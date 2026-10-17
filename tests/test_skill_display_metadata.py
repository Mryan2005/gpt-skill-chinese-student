from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "plugin" / "skills"


class SkillDisplayMetadataTests(unittest.TestCase):
    def test_every_plugin_skill_has_namespaced_picker_display_name(self) -> None:
        skill_dirs = sorted(path for path in SKILLS_ROOT.iterdir() if path.is_dir())
        self.assertIn("profile", {path.name for path in skill_dirs})
        for skill_dir in skill_dirs:
            metadata = skill_dir / "agents" / "openai.yaml"
            self.assertTrue(metadata.is_file(), skill_dir.name)
            text = metadata.read_text(encoding="utf-8")
            match = re.search(r'^\s*display_name:\s*["\']([^"\']+)["\']', text, re.MULTILINE)
            self.assertIsNotNone(match, skill_dir.name)
            self.assertEqual(match.group(1), f"$中式学生:{skill_dir.name}")

    def test_default_prompt_uses_combined_skill_identity(self) -> None:
        for skill_dir in sorted(path for path in SKILLS_ROOT.iterdir() if path.is_dir()):
            text = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertIn(f"$chinese-student:{skill_dir.name}", text)

    def test_internal_skill_ids_remain_slugs(self) -> None:
        for skill_dir in SKILLS_ROOT.iterdir():
            if not skill_dir.is_dir():
                continue
            frontmatter = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            self.assertRegex(frontmatter, rf"(?m)^name: {re.escape(skill_dir.name)}$")


if __name__ == "__main__":
    unittest.main()
