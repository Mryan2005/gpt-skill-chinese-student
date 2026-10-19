from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HELP_ROOT = REPO_ROOT / "plugin" / "skills" / "help"
sys.path.insert(0, str(HELP_ROOT / "scripts"))

from help import load_registry, render_help, validate_registry  # noqa: E402


class HelpStructureTests(unittest.TestCase):
    def test_registry_covers_live_skills(self) -> None:
        self.assertEqual(validate_registry(HELP_ROOT, HELP_ROOT.parent), [])

    def test_default_help_is_compact_and_lists_domain_models(self) -> None:
        output = render_help(load_registry(HELP_ROOT, HELP_ROOT.parent))
        self.assertIn("chinese-student: review", output)
        self.assertIn("chinese-student: practice", output)
        self.assertIn("chinese-student: exam", output)
        self.assertIn("study-math", output)
        self.assertIn("domain-model", output)

    def test_detail_and_subcommand_help_are_read_only_descriptions(self) -> None:
        registry = load_registry(HELP_ROOT, HELP_ROOT.parent)
        review = render_help(registry, "review")
        user_written = render_help(registry, "review", "user-written")
        self.assertIn("questions.pdf", review)
        self.assertIn("user-submission.pdf", user_written)
        self.assertIn("不生成 PDF", review)

    def test_exam_hit_help_is_explicitly_question_by_question(self) -> None:
        detail = render_help(load_registry(HELP_ROOT, HELP_ROOT.parent), "exam", "hit")
        self.assertIn("HIT/PARTIAL/MISS/UNRESOLVED", detail)
        self.assertIn("每道题", detail)

    def test_all_help_expands_every_command(self) -> None:
        output = render_help(load_registry(HELP_ROOT, HELP_ROOT.parent), all_commands=True)
        self.assertIn("chinese-student: relearn", output)
        self.assertIn("requires explicit user confirmation", output)

    def test_unknown_command_suggests_without_execution(self) -> None:
        output = render_help(load_registry(HELP_ROOT, HELP_ROOT.parent), "revie")
        self.assertIn("Unknown", output)
        self.assertIn("review", output)


if __name__ == "__main__":
    unittest.main()
