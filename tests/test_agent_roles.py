from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugin"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "skills" / "check" / "scripts"))

from agent_roles import load_agent_role_registry, validate_agent_role_registry  # noqa: E402
from plan_execution import plan_execution  # noqa: E402


class AgentRoleRegistryTests(unittest.TestCase):
    def load(self) -> dict:
        return load_agent_role_registry(PLUGIN_ROOT)

    def test_every_predeclared_role_contract_is_valid(self) -> None:
        registry = self.load()
        self.assertEqual(validate_agent_role_registry(registry, PLUGIN_ROOT), [])
        self.assertEqual({workflow["skill"] for workflow in registry["workflows"]}, {"learn", "exam", "review", "check", "fix"})

    def test_each_workflow_has_one_serialized_merger(self) -> None:
        for workflow in self.load()["workflows"]:
            with self.subTest(skill=workflow["skill"]):
                mergers = [role for role in workflow["roles"] if role["kind"] == "merger"]
                self.assertEqual(len(mergers), 1)
                self.assertEqual(mergers[0]["id"], workflow["mergerRole"])
                self.assertFalse(mergers[0]["parallelizable"])

    def test_exam_answerer_cannot_receive_hit_or_graph_context(self) -> None:
        workflow = next(item for item in self.load()["workflows"] if item["skill"] == "exam")
        answerer = next(role for role in workflow["roles"] if role["id"] == "independent-answerer")
        self.assertEqual(answerer["reads"], ["original-question-only"])

    def test_non_merger_canonical_write_is_rejected(self) -> None:
        registry = copy.deepcopy(self.load())
        workflow = next(item for item in registry["workflows"] if item["skill"] == "fix")
        fixer = next(role for role in workflow["roles"] if role["id"] == "schema-fixer")
        fixer["writes"] = ["derived-artifact"]
        errors = validate_agent_role_registry(registry, PLUGIN_ROOT)
        self.assertTrue(any("schema-fixer isolated role writes" in error for error in errors))

    def test_check_execution_plan_consumes_registry_bundles(self) -> None:
        workflow = next(item for item in self.load()["workflows"] if item["skill"] == "check")
        self.assertEqual(plan_execution(3)["bundles"], workflow["bundles"])


if __name__ == "__main__":
    unittest.main()
