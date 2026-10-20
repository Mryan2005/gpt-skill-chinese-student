from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugin"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from route_command import route_command  # noqa: E402
from skill_registry import load_registry, validate_route_result  # noqa: E402


REGISTRY = load_registry(PLUGIN_ROOT)


class CommandRoutingTests(unittest.TestCase):
    def route(self, text: str) -> dict:
        result = route_command(text, registry=REGISTRY)
        self.assertEqual(validate_route_result(result), [], text)
        return result

    def test_routes_workflows_to_canonical_invocations(self) -> None:
        cases = {
            "学习数学章节": ("learn", None, "learn-topic", "study-math"),
            "检查知识库": ("check", None, None, None),
            "根据检查报告自动修复": ("fix", None, None, None),
            "考后复盘这套试卷": ("review", "exam-result", None, None),
            "考后复盘我的答卷": ("review", "user-written", None, None),
            "用试卷检查知识覆盖": ("exam", None, None, None),
            "用新手体验测试这个站": ("heal", None, None, None),
            "优化图谱去重": ("optimize", "analyze", None, None),
            "今晚优先复习": ("sort", "tonight", None, None),
            "生成一套练习题": ("practice", None, None, None),
            "更新插件 schema": ("update", None, None, None),
            "重学数学": ("relearn", None, None, "study-math"),
            "记录我容易忘记条件": ("profile", None, None, None),
            "我发现这张卡错了": ("amend", None, None, None),
            "帮助": ("help", None, None, None),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                result = self.route(text)
                self.assertEqual(result["command"], expected[0])
                self.assertEqual(result["subcommand"], expected[1])
                self.assertEqual(result["playbook"], expected[2])
                self.assertEqual(result["domainModel"], expected[3])
                self.assertEqual(result["canonicalInvocation"], f"$chinese-student:{expected[0]}")

    def test_explicit_internal_domain_model_routes_through_learn(self) -> None:
        result = self.route("$chinese-student:study-math")
        self.assertEqual(result["command"], "learn")
        self.assertEqual(result["domainModel"], "study-math")
        self.assertEqual(result["canonicalInvocation"], "$chinese-student:learn")
        self.assertFalse(result["requiresClarification"])

    def test_explicit_skill_identity_wins_over_natural_language_signals(self) -> None:
        result = self.route("$chinese-student:check 请不要修改内容")
        self.assertEqual(result["command"], "check")
        self.assertEqual(result["confidence"], "high")
        self.assertEqual(result["candidates"][0]["score"], 1000)

    def test_unknown_request_does_not_guess_a_workflow(self) -> None:
        result = self.route("帮我看看这个")
        self.assertIsNone(result["command"])
        self.assertTrue(result["requiresClarification"])
        self.assertEqual(result["confidence"], "none")


if __name__ == "__main__":
    unittest.main()
