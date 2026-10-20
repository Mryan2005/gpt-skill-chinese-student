"""Load and validate the predeclared Agent Role Registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REGISTRY_RELATIVE_PATH = Path("references") / "agent-role-registry.v1.json"
ROLE_KINDS = {"isolated-reader", "isolated-proposer", "merger"}
FALLBACKS = {"orchestrator-sequential", "single-coordinator"}
WORKFLOW_WRITES = {
    "learn": {"canonical-subject", "learning-state"},
    "exam": {"exam-workspace", "frozen-exam-result"},
    "review": {"review-workspace", "eligible-learner-update"},
    "check": {"check-workspace"},
    "fix": {"derived-artifact", "runtime-artifact", "generated-artifact"},
}
ISOLATED_WRITES = {
    "learn": {"learn-report"},
    "exam": {"exam-workspace"},
    "review": {"review-report"},
    "check": {"check-report"},
    "fix": {"fix-proposal"},
}


def load_agent_role_registry(plugin_root: Path) -> dict[str, Any]:
    return json.loads((plugin_root / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_non_empty_text(item) for item in value)


def validate_agent_role_registry(registry: dict[str, Any], plugin_root: Path) -> list[str]:
    errors: list[str] = []
    if registry.get("schemaVersion") != "agent-role-registry.v1":
        errors.append("agent role registry schemaVersion must be agent-role-registry.v1")
    workflows = registry.get("workflows")
    if not isinstance(workflows, list) or not workflows:
        return errors + ["agent role registry workflows must be a non-empty array"]
    seen_skills: set[str] = set()
    skills_root = plugin_root / "skills"
    for workflow_index, workflow in enumerate(workflows):
        path = f"workflows[{workflow_index}]"
        if not isinstance(workflow, dict):
            errors.append(f"{path} must be an object")
            continue
        skill = workflow.get("skill")
        if not _non_empty_text(skill):
            errors.append(f"{path}.skill must be non-empty")
            continue
        if skill in seen_skills:
            errors.append(f"agent roles duplicate workflow {skill}")
        seen_skills.add(skill)
        if not (skills_root / skill / "SKILL.md").is_file():
            errors.append(f"agent roles reference unknown skill {skill}")
        if workflow.get("fallback") not in FALLBACKS:
            errors.append(f"{skill}.fallback is invalid")
        roles = workflow.get("roles")
        if not isinstance(roles, list) or len(roles) < 2:
            errors.append(f"{skill}.roles must contain at least two roles")
            continue
        role_ids = [role.get("id") for role in roles if isinstance(role, dict)]
        if len(role_ids) != len(roles) or any(not _non_empty_text(role_id) for role_id in role_ids):
            errors.append(f"{skill}.roles need non-empty ids")
        if len(role_ids) != len(set(role_ids)):
            errors.append(f"{skill}.role ids must be unique")
        merger_id = workflow.get("mergerRole")
        mergers = [role for role in roles if isinstance(role, dict) and role.get("kind") == "merger"]
        if len(mergers) != 1 or not _non_empty_text(merger_id) or mergers[0].get("id") != merger_id:
            errors.append(f"{skill} must declare exactly one matching mergerRole")
        for role_index, role in enumerate(roles):
            role_path = f"{skill}.roles[{role_index}]"
            if not isinstance(role, dict):
                errors.append(f"{role_path} must be an object")
                continue
            role_id = role.get("id", "<unknown>")
            if role.get("kind") not in ROLE_KINDS:
                errors.append(f"{role_path}.kind is invalid")
            contract = role.get("contract")
            if not _non_empty_text(contract) or not (plugin_root / str(contract)).is_file():
                errors.append(f"{skill}.{role_id} contract file is missing")
            elif not (plugin_root / str(contract)).read_text(encoding="utf-8").lstrip().startswith("#"):
                errors.append(f"{skill}.{role_id} contract must be Markdown")
            if not _text_list(role.get("reads")):
                errors.append(f"{skill}.{role_id}.reads must be a non-empty string array")
            if not _text_list(role.get("writes")):
                errors.append(f"{skill}.{role_id}.writes must be a non-empty string array")
            if not _non_empty_text(role.get("output")):
                errors.append(f"{skill}.{role_id}.output must be non-empty")
            if not isinstance(role.get("parallelizable"), bool):
                errors.append(f"{skill}.{role_id}.parallelizable must be boolean")
            writes = set(role.get("writes", [])) if isinstance(role.get("writes"), list) else set()
            if role.get("kind") == "merger":
                if role.get("parallelizable"):
                    errors.append(f"{skill}.{role_id} merger must serialize writes")
                if writes != WORKFLOW_WRITES.get(skill, set()):
                    errors.append(f"{skill}.{role_id} merger writes do not match workflow boundary")
            elif writes != ISOLATED_WRITES.get(skill, set()):
                errors.append(f"{skill}.{role_id} isolated role writes must stay in its isolated boundary")
        role_by_id = {role.get("id"): role for role in roles if isinstance(role, dict)}
        bundles = workflow.get("bundles")
        if skill == "check":
            if not isinstance(bundles, dict) or not bundles:
                errors.append("check must declare non-empty auditor bundles")
            else:
                bundled_roles = [role_id for bundle in bundles.values() if isinstance(bundle, list) for role_id in bundle]
                required_roles = {role_id for role_id in role_ids if role_id != merger_id}
                if set(bundled_roles) != required_roles or len(bundled_roles) != len(set(bundled_roles)):
                    errors.append("check bundles must contain every non-merger role exactly once")
                if merger_id in bundled_roles:
                    errors.append("check merger must not be scheduled as an auditor bundle")
        if skill == "exam":
            answerer = role_by_id.get("independent-answerer", {})
            forbidden = {"frozen-subject-snapshot", "frozen-hit-records", "original-explanation-pdf"}
            if set(answerer.get("reads", [])) != {"original-question-only"} or forbidden & set(answerer.get("reads", [])):
                errors.append("exam.independent-answerer must receive only original-question-only")
            inspector = role_by_id.get("hit-inspector", {})
            if "frozen-subject-snapshot" not in inspector.get("reads", []):
                errors.append("exam.hit-inspector must read the frozen-subject-snapshot")
        if skill == "review":
            learner = role_by_id.get("learner-reviewer", {})
            if "eligible-learner-update" in learner.get("writes", []):
                errors.append("review.learner-reviewer must propose, not directly write Learner State")
    return errors
