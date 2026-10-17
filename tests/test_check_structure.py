from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "check"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_findings import validate_report  # noqa: E402
from validate_agent_reports import validate_agent_report  # noqa: E402
from plan_execution import plan_execution  # noqa: E402
from validate_source_derived import validate_record as validate_source_derived  # noqa: E402
from reset_check_workspace import reset_workspace, validate_target  # noqa: E402


PLAYBOOKS = {
    "full-audit.md",
    "source-audit.md",
    "structure-audit.md",
    "coverage-audit.md",
    "content-audit.md",
    "question-audit.md",
    "solution-audit.md",
    "math-audit.md",
    "latex-audit.md",
    "relation-audit.md",
    "provenance-audit.md",
    "rendering-audit.md",
    "retrieval-audit.md",
    "readiness-audit.md",
    "learner-model-audit.md",
    "sort-audit.md",
}

REFERENCES = {
    "common.md",
    "audit-contract.md",
    "execution-contract.md",
    "check-workspace.md",
    "finding-schema.md",
    "severity.md",
}

AGENTS = {
    "source-auditor.md",
    "structure-auditor.md",
    "content-auditor.md",
    "coverage-auditor.md",
    "question-auditor.md",
    "solution-auditor.md",
    "math-auditor.md",
    "latex-auditor.md",
    "relation-auditor.md",
    "provenance-auditor.md",
    "rendering-auditor.md",
    "retrieval-auditor.md",
    "finding-merger.md",
    "learner-model-auditor.md",
    "sort-state-auditor.md",
}


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


class CheckStructureTests(unittest.TestCase):
    def test_front_door_is_small_and_routes_every_audit(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 80)
        for name in PLAYBOOKS:
            self.assertTrue((SKILL_ROOT / "playbooks" / name).is_file(), name)

    def test_audit_references_exist(self) -> None:
        for name in REFERENCES:
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)

    def test_specialized_auditors_and_merger_exist(self) -> None:
        for name in AGENTS:
            self.assertTrue((SKILL_ROOT / "agents" / name).is_file(), name)

    def test_execution_planner_degrades_without_skipping_roles(self) -> None:
        self.assertEqual(plan_execution(3)["actualMode"], "parallel-agent")
        self.assertEqual(plan_execution(2)["actualMode"], "batched-agent")
        self.assertEqual(plan_execution(1)["actualMode"], "shared-agent")
        fallback = plan_execution(0)
        self.assertEqual(fallback["actualMode"], "orchestrator-fallback")
        self.assertEqual(fallback["batches"], [["structure", "domain", "presentation", "coverage"]])
        disabled = plan_execution(3, 2)
        self.assertTrue(disabled["spawningDisabled"])
        self.assertEqual(disabled["actualMode"], "orchestrator-fallback")

    def test_entrypoint_and_playbook_links_resolve(self) -> None:
        documents = [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "playbooks").glob("*.md"))
        for document in documents:
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_finding_report_passes(self) -> None:
        report_path = SKILL_ROOT / "examples" / "finding-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_report(report), [])

    def test_finding_report_rejects_mutation_or_wrong_summary(self) -> None:
        report_path = SKILL_ROOT / "examples" / "finding-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(report)
        mutated["readOnly"] = False
        mutated["summary"]["blocker"] = 0
        errors = validate_report(mutated)
        self.assertTrue(any("readOnly" in error for error in errors))
        self.assertTrue(any("summary.blocker" in error for error in errors))

    def test_finding_report_requires_root_layer_and_result(self) -> None:
        report_path = SKILL_ROOT / "examples" / "finding-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["findings"][0].pop("rootLayer")
        report["result"] = "PASS"
        errors = validate_report(report)
        self.assertTrue(any("rootLayer" in error for error in errors))
        self.assertTrue(any("expected FAIL" in error for error in errors))

    def test_capacity_fallback_does_not_block_a_completed_audit(self) -> None:
        report_path = SKILL_ROOT / "examples" / "finding-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["execution"].update(
            {
                "actualMode": "orchestrator-fallback",
                "maxParallel": 0,
                "spawnFailures": 2,
                "spawningDisabled": True,
                "fallbackReason": "spawn-failure-threshold",
            }
        )
        for audit in report["run"]["auditStatuses"]:
            audit["executionMode"] = "orchestrator-fallback"
        self.assertEqual(validate_report(report), [])

    def test_finding_report_rejects_residual_workspace(self) -> None:
        report_path = SKILL_ROOT / "examples" / "finding-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["workspace"]["residualPaths"] = ["findings.json"]
        errors = validate_report(report)
        self.assertTrue(any("CHECK_WORKSPACE_NOT_CLEAN" in error for error in errors))

    def test_isolated_agent_report_passes(self) -> None:
        report_path = SKILL_ROOT / "examples" / "agent-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(
            validate_agent_report(
                report,
                expected_run_id="math-1-check-001",
                expected_artifact_version="math-records.example.v1",
            ),
            [],
        )

    def test_isolated_agent_report_rejects_stale_run(self) -> None:
        report_path = SKILL_ROOT / "examples" / "agent-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        errors = validate_agent_report(report, expected_run_id="new-run")
        self.assertTrue(any("STALE_AGENT_REPORT" in error for error in errors))

    def test_isolated_agent_report_rejects_misattribution(self) -> None:
        report_path = SKILL_ROOT / "examples" / "agent-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["findings"][0]["reportedBy"] = "structure-auditor"
        errors = validate_agent_report(report)
        self.assertTrue(any("reportedBy must match" in error for error in errors))

    def test_source_derived_sample_passes(self) -> None:
        report_path = SKILL_ROOT / "examples" / "source-derived-record.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_source_derived(report), [])

    def test_source_derived_collapse_fails(self) -> None:
        report_path = SKILL_ROOT / "examples" / "source-derived-record.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["derived"][0]["sourceText"] = "错误地复制的原文"
        errors = validate_source_derived(report)
        self.assertTrue(any("SOURCE_AND_DERIVED_COLLAPSED" in error for error in errors))

    def test_reset_script_deletes_only_the_exact_current_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / ".check" / "current"
            root.mkdir(parents=True)
            (root / "old-findings.json").write_text("old", encoding="utf-8")
            target = validate_target(str(root))
            reset_workspace(target, True)
            self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
