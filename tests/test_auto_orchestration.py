from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTO_ROOT = REPO_ROOT / "plugin" / "skills" / "auto"
sys.path.insert(0, str(AUTO_ROOT / "scripts"))

from auto_engine import (  # noqa: E402
    PLUGIN_ROOT,
    apply_step_result,
    build_plan,
    initialize_run,
    load_run,
    refresh_state,
    validate_plan,
)
from skill_registry import load_registry  # noqa: E402


class AutoOrchestrationTests(unittest.TestCase):
    def plan(self, request: dict, run_id: str = "auto-test-001") -> dict:
        plan = build_plan(request, run_id=run_id)
        self.assertEqual(validate_plan(plan, registry=load_registry(PLUGIN_ROOT)), [])
        return plan

    def test_compound_request_builds_dependency_aware_plan(self) -> None:
        plan = self.plan({"request": "学习这些资料，然后检查并修复", "sourcePaths": ["notes.pdf"]})
        self.assertEqual([step["skill"] for step in plan["steps"]], ["learn", "check", "fix", "check"])
        self.assertEqual(plan["steps"][2]["dependsOn"], [plan["steps"][1]["id"]])
        self.assertEqual(plan["steps"][-1]["dependsOn"], [plan["steps"][2]["id"]])

    def test_public_skill_contract_and_example_exist(self) -> None:
        self.assertTrue((AUTO_ROOT / "SKILL.md").is_file())
        self.assertTrue((AUTO_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue((AUTO_ROOT / "references" / "auto-contract.md").is_file())
        example = json.loads((AUTO_ROOT / "examples" / "compound-request.json").read_text(encoding="utf-8"))
        plan = self.plan(example, "auto-example")
        self.assertEqual([step["skill"] for step in plan["steps"]], ["learn", "check", "fix", "check"])

    def test_single_goal_does_not_expand_to_a_pipeline(self) -> None:
        plan = self.plan({"request": "检查知识库"})
        self.assertEqual(len(plan["steps"]), 1)
        self.assertEqual(plan["steps"][0]["skill"], "check")

    def test_fix_inserts_fresh_check_and_independent_recheck(self) -> None:
        plan = self.plan({"request": "自动修复这些问题"})
        self.assertEqual([step["skill"] for step in plan["steps"]], ["check", "fix", "check"])

    def test_missing_referenced_source_is_blocked_without_inventing_evidence(self) -> None:
        plan = self.plan({"request": "学习这些资料"})
        self.assertEqual(plan["steps"], [])
        self.assertEqual(plan["blocked"][0]["code"], "AUTO_SOURCE_REQUIRED")

    def test_relearn_requires_explicit_authorization(self) -> None:
        plan = self.plan({"request": "重学数学"})
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            state = initialize_run(workspace, plan)
            state = refresh_state(plan, state, workspace)
        self.assertEqual(state["steps"][0]["status"], "BLOCKED")
        self.assertEqual(state["steps"][0]["blockers"][0]["code"], "AUTO_AUTHORIZATION_REQUIRED")

    def test_real_artifact_and_actual_validator_are_required_for_completion(self) -> None:
        plan = self.plan({"request": "检查知识库"}, "auto-test-actual")
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            initialize_run(workspace, plan)
            artifact = workspace / "findings.json"
            artifact.write_text("{}", encoding="utf-8")
            result = {
                "schemaVersion": "auto.step-result.v1",
                "stepId": plan["steps"][0]["id"],
                "skill": "check",
                "invocation": "$chinese-student:check",
                "status": "SUCCEEDED",
                "startedAt": "2026-10-20T16:00:00Z",
                "completedAt": "2026-10-20T16:01:00Z",
                "outputArtifacts": [{"path": "findings.json"}],
                "validatorCommands": [[sys.executable, str(PLUGIN_ROOT / "scripts" / "validate_agent_roles.py")]],
            }
            state = apply_step_result(workspace, plan["runId"], result)
            self.assertEqual(state["status"], "COMPLETE")
            self.assertEqual(state["steps"][0]["status"], "SUCCEEDED")

    def test_resume_marks_changed_output_as_stale(self) -> None:
        plan = self.plan({"request": "检查知识库"}, "auto-test-stale")
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            initialize_run(workspace, plan)
            artifact = workspace / "findings.json"
            artifact.write_text("{}", encoding="utf-8")
            result = {
                "schemaVersion": "auto.step-result.v1", "stepId": plan["steps"][0]["id"], "skill": "check", "invocation": "$chinese-student:check", "status": "SUCCEEDED", "startedAt": "2026-10-20T16:00:00Z", "completedAt": "2026-10-20T16:01:00Z", "outputArtifacts": [{"path": "findings.json"}], "validatorCommands": [[sys.executable, str(PLUGIN_ROOT / "scripts" / "validate_agent_roles.py")]]
            }
            apply_step_result(workspace, plan["runId"], result)
            artifact.write_text('{"changed":true}', encoding="utf-8")
            loaded_plan, state, _ = load_run(workspace, plan["runId"])
            state = refresh_state(loaded_plan, state, workspace)
        self.assertEqual(state["steps"][0]["status"], "STALE")
        self.assertEqual(state["status"], "BLOCKED")

    def test_stale_check_result_replans_bounded_fix(self) -> None:
        plan = self.plan({"request": "自动修复这些问题"}, "auto-test-replan")
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            initialize_run(workspace, plan)
            _plan, state, state_path = load_run(workspace, plan["runId"])
            state["steps"][0]["status"] = "SUCCEEDED"
            state["steps"][1]["status"] = "READY"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            result = {
                "schemaVersion": "auto.step-result.v1", "stepId": plan["steps"][1]["id"], "skill": "fix", "invocation": "$chinese-student:fix", "status": "FAILED", "failureCode": "STALE_CHECK_REPORT", "startedAt": "2026-10-20T16:00:00Z", "completedAt": "2026-10-20T16:01:00Z", "outputArtifacts": [], "validatorCommands": []
            }
            state = apply_step_result(workspace, plan["runId"], result)
        self.assertEqual(state["steps"][0]["status"], "READY")
        self.assertEqual(state["steps"][1]["status"], "PENDING")
        self.assertEqual(state["replanHistory"][-1]["status"], "REPLAN")


if __name__ == "__main__":
    unittest.main()
