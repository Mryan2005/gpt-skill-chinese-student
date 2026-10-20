"""Evidence-gated state engine for the Chinese Student Auto orchestrator."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from skill_registry import load_registry, route_command, validate_registry  # noqa: E402


PLAN_VERSION = "auto.plan.v1"
STATE_VERSION = "auto.run-state.v1"
RESULT_VERSION = "auto.step-result.v1"
STEP_STATES = {"PENDING", "READY", "RUNNING", "SUCCEEDED", "FAILED", "BLOCKED", "STALE"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_help_index(plugin_root: Path = PLUGIN_ROOT) -> dict[str, dict[str, Any]]:
    index = json.loads((plugin_root / "skills" / "help" / "references" / "command-index.json").read_text(encoding="utf-8"))
    return {str(item["name"]): item for item in index["commands"]}


def _split_goals(request: dict[str, Any]) -> list[str]:
    explicit = request.get("goals")
    if isinstance(explicit, list) and explicit:
        values = [item.get("request") if isinstance(item, dict) else item for item in explicit]
        return [value.strip() for value in values if isinstance(value, str) and value.strip()]
    text = request.get("request")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("request must be non-empty")
    fragments = [part.strip() for part in re.split(r"(?:然后|接着|之后|并且|再将|再)", text) if part.strip()]
    return fragments or [text.strip()]


def _authorization(skill: str, subcommand: str | None) -> str:
    if skill == "relearn":
        return "explicit-destructive-confirmation"
    if skill == "optimize" and subcommand == "apply":
        return "explicit-apply-confirmation"
    if skill == "fix":
        return "user-called-auto-authorizes-allowed-repairs"
    return "none"


def _step(step_id: str, route: dict[str, Any], detail: dict[str, Any], dependencies: list[str]) -> dict[str, Any]:
    skill = route["command"]
    return {
        "id": step_id,
        "skill": skill,
        "invocation": route["canonicalInvocation"],
        "subcommand": route.get("subcommand"),
        "playbook": route.get("playbook"),
        "domainModel": route.get("domainModel"),
        "purpose": detail["description"],
        "inputArtifacts": detail.get("inputs", []),
        "dependsOn": dependencies,
        "expectedOutputs": detail.get("outputs", []),
        "preconditions": ["dependencies succeeded", "input artifacts are fresh", "delegated Skill contract accepts the operation"],
        "completionCriteria": ["actual output artifacts exist", "declared validators pass", "delegated Skill acceptance criteria are satisfied"],
        "allowedWrites": detail.get("sideEffects", []),
        "requiredAuthorization": _authorization(skill, route.get("subcommand")),
        "failurePolicy": {"maxAttempts": 2, "onStaleInput": "replan", "onInsufficientEvidence": "block", "onNoProgress": "stop"},
    }


def build_plan(request: dict[str, Any], *, plugin_root: Path = PLUGIN_ROOT, run_id: str | None = None) -> dict[str, Any]:
    registry = load_registry(plugin_root)
    errors = validate_registry(registry, plugin_root)
    if errors:
        raise ValueError("invalid skill registry: " + " | ".join(errors))
    help_index = load_help_index(plugin_root)
    run_id = run_id or str(request.get("runId") or f"auto-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    routes: list[tuple[str, dict[str, Any]]] = []
    for goal in _split_goals(request):
        route = route_command(goal, registry=registry, subject=request.get("subject"))
        if route.get("command") in {None, "auto"}:
            continue
        if route["command"] not in help_index or help_index[route["command"]].get("kind") != "workflow":
            continue
        routes.append((goal, route))
    if not routes:
        return {"schemaVersion": PLAN_VERSION, "runId": run_id, "request": request.get("request", ""), "goals": [], "steps": [], "acceptanceCriteria": [], "blocked": [{"code": "AUTO_INTENT_UNRESOLVED", "reason": "No existing public workflow matched the request."}]}

    source_hints = ("资料", "教材", "笔记", "图片", "pdf", "照片")
    has_sources = bool(request.get("sourcePaths") or request.get("artifacts"))
    missing_source_goals = [goal for goal, route in routes if route["command"] == "learn" and any(hint in goal.casefold() for hint in source_hints) and not has_sources]
    if missing_source_goals:
        return {"schemaVersion": PLAN_VERSION, "runId": run_id, "request": request.get("request", ""), "goals": [{"request": goal, "route": route} for goal, route in routes], "steps": [], "acceptanceCriteria": [], "blocked": [{"code": "AUTO_SOURCE_REQUIRED", "goals": missing_source_goals, "reason": "Referenced learning material was not supplied; auto will not invent Source evidence."}]}

    steps: list[dict[str, Any]] = []
    completed_dependencies: list[str] = []
    index = 1
    for goal, route in routes:
        skill = route["command"]
        if skill == "fix" and not any(item["skill"] == "check" for item in steps):
            check_route = {"command": "check", "canonicalInvocation": "$chinese-student:check", "subcommand": "full-audit", "playbook": None, "domainModel": route.get("domainModel")}
            check_step = _step(f"step-{index:02d}-check", check_route, help_index["check"], completed_dependencies)
            check_step["purpose"] = "Produce the fresh check evidence required before fix."
            steps.append(check_step)
            completed_dependencies = [check_step["id"]]
            index += 1
        item = _step(f"step-{index:02d}-{skill}", route, help_index[skill], completed_dependencies)
        item["goal"] = goal
        steps.append(item)
        completed_dependencies = [item["id"]]
        index += 1
        if skill == "fix":
            verify_route = {"command": "check", "canonicalInvocation": "$chinese-student:check", "subcommand": "full-audit", "playbook": None, "domainModel": route.get("domainModel")}
            verify_step = _step(f"step-{index:02d}-check", verify_route, help_index["check"], completed_dependencies)
            verify_step["purpose"] = "Independently verify the repairs; never treat fix-local validation as a full audit."
            steps.append(verify_step)
            completed_dependencies = [verify_step["id"]]
            index += 1
    return {
        "schemaVersion": PLAN_VERSION,
        "runId": run_id,
        "request": request.get("request", ""),
        "goals": [{"request": goal, "route": route} for goal, route in routes],
        "steps": steps,
        "acceptanceCriteria": ["every planned step has successful real output and validation evidence", "all user goals are satisfied, partially satisfied, or explicitly blocked"],
        "blocked": [],
    }


def validate_plan(plan: dict[str, Any], *, registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("schemaVersion") != PLAN_VERSION:
        errors.append("schemaVersion must be auto.plan.v1")
    if not isinstance(plan.get("runId"), str) or not plan["runId"].strip():
        errors.append("runId must be non-empty")
    steps = plan.get("steps")
    if not isinstance(steps, list):
        return errors + ["steps must be an array"]
    known = {entry["id"] for entry in registry["commands"] if entry.get("visibility") == "user" and entry["id"] != "auto"}
    ids: set[str] = set()
    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("id"), str):
            errors.append("every step needs an id")
            continue
        if step["id"] in ids:
            errors.append(f"duplicate step id {step['id']}")
        ids.add(step["id"])
        if step.get("skill") not in known:
            errors.append(f"{step['id']} must target an existing public non-auto workflow")
        if step.get("invocation") != f"$chinese-student:{step.get('skill')}":
            errors.append(f"{step['id']} has an invalid invocation")
        if step.get("skill") == "relearn" and step.get("requiredAuthorization") != "explicit-destructive-confirmation":
            errors.append(f"{step['id']} must retain relearn confirmation")
        if step.get("skill") == "optimize" and step.get("subcommand") == "apply" and step.get("requiredAuthorization") != "explicit-apply-confirmation":
            errors.append(f"{step['id']} must retain optimize apply confirmation")
    for step in steps:
        for dependency in step.get("dependsOn", []):
            if dependency not in ids:
                errors.append(f"{step.get('id')} depends on unknown step {dependency}")
    return errors


def _run_dir(workspace: Path, run_id: str) -> Path:
    return workspace / ".auto" / run_id


def initialize_run(workspace: Path, plan: dict[str, Any], *, authorizations: list[str] | None = None) -> dict[str, Any]:
    run_dir = _run_dir(workspace, plan["runId"])
    run_dir.mkdir(parents=True, exist_ok=True)
    plan_path = run_dir / "plan.json"
    serialized = canonical_json(plan)
    if plan_path.exists() and plan_path.read_text(encoding="utf-8") != serialized:
        raise ValueError("AUTO_RUN_ID_COLLISION: existing run has a different plan")
    plan_path.write_text(serialized, encoding="utf-8")
    state_path = run_dir / "state.json"
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    state = {
        "schemaVersion": STATE_VERSION,
        "runId": plan["runId"],
        "planHash": "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        "workspace": str(workspace.resolve()),
        "status": "PLANNED",
        "authorizations": sorted(set(authorizations or [])),
        "steps": [{"id": step["id"], "status": "PENDING", "attempts": 0, "artifacts": [], "validationEvidence": [], "blockers": []} for step in plan["steps"]],
        "replanHistory": [],
    }
    state_path.write_text(canonical_json(state), encoding="utf-8")
    return state


def load_run(workspace: Path, run_id: str) -> tuple[dict[str, Any], dict[str, Any], Path]:
    run_dir = _run_dir(workspace, run_id)
    plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    return plan, state, state_path


def _authorized(step: dict[str, Any], state: dict[str, Any]) -> bool:
    required = step["requiredAuthorization"]
    return required in {"none", "user-called-auto-authorizes-allowed-repairs"} or required in state.get("authorizations", [])


def refresh_state(plan: dict[str, Any], state: dict[str, Any], workspace: Path) -> dict[str, Any]:
    by_id = {item["id"]: item for item in state["steps"]}
    for item in state["steps"]:
        if item["status"] == "SUCCEEDED":
            for artifact in item.get("artifacts", []):
                path = workspace / artifact["path"]
                if not path.is_file() or sha256(path) != artifact["sha256"]:
                    item["status"] = "STALE"
                    item["blockers"] = [{"code": "AUTO_ARTIFACT_STALE", "artifact": artifact["path"]}]
    for step in plan["steps"]:
        item = by_id[step["id"]]
        if item["status"] in {"SUCCEEDED", "FAILED", "BLOCKED", "STALE"}:
            continue
        dependencies = [by_id[dependency]["status"] for dependency in step.get("dependsOn", [])]
        if any(status in {"FAILED", "BLOCKED", "STALE"} for status in dependencies):
            item["status"] = "BLOCKED"
            item["blockers"] = [{"code": "AUTO_PREREQUISITE_NOT_SATISFIED"}]
        elif not _authorized(step, state):
            item["status"] = "BLOCKED"
            item["blockers"] = [{"code": "AUTO_AUTHORIZATION_REQUIRED", "required": step["requiredAuthorization"]}]
        elif all(status == "SUCCEEDED" for status in dependencies):
            item["status"] = "READY"
    statuses = {item["status"] for item in state["steps"]}
    state["status"] = "COMPLETE" if statuses == {"SUCCEEDED"} else "BLOCKED" if statuses & {"BLOCKED", "STALE"} else "FAILED" if "FAILED" in statuses else "RUNNING"
    return state


def _artifact_evidence(workspace: Path, artifacts: list[dict[str, Any]]) -> list[dict[str, str]]:
    recorded: list[dict[str, str]] = []
    for artifact in artifacts:
        path_text = artifact.get("path") if isinstance(artifact, dict) else None
        if not isinstance(path_text, str) or not path_text.strip():
            raise ValueError("AUTO_OUTPUT_ARTIFACT_MISSING_PATH")
        path = (workspace / path_text).resolve()
        if workspace.resolve() not in path.parents or not path.is_file():
            raise ValueError(f"AUTO_OUTPUT_ARTIFACT_MISSING: {path_text}")
        recorded.append({"path": str(path.relative_to(workspace.resolve())), "sha256": sha256(path)})
    if not recorded:
        raise ValueError("AUTO_OUTPUT_ARTIFACT_REQUIRED")
    return recorded


def _run_validators(commands: list[list[str]], workspace: Path) -> list[dict[str, Any]]:
    if not commands:
        raise ValueError("AUTO_VALIDATION_REQUIRED")
    evidence: list[dict[str, Any]] = []
    for command in commands:
        if not isinstance(command, list) or not command or not all(isinstance(part, str) for part in command):
            raise ValueError("AUTO_VALIDATOR_COMMAND_INVALID")
        executable = Path(command[0]).name.casefold()
        script = next((Path(part).resolve() for part in command[1:] if part.endswith(".py")), None)
        if not executable.startswith("python") or script is None or PLUGIN_ROOT not in script.parents or not script.name.startswith("validate_"):
            raise ValueError("AUTO_VALIDATOR_COMMAND_FORBIDDEN")
        result = subprocess.run(command, cwd=workspace, text=True, capture_output=True, check=False)
        evidence.append({"command": command, "exitCode": result.returncode, "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:]})
        if result.returncode != 0:
            raise ValueError("AUTO_VALIDATION_FAILED")
    return evidence


def apply_step_result(workspace: Path, run_id: str, result: dict[str, Any]) -> dict[str, Any]:
    plan, state, state_path = load_run(workspace, run_id)
    state = refresh_state(plan, state, workspace)
    if result.get("schemaVersion") != RESULT_VERSION:
        raise ValueError("AUTO_STEP_RESULT_SCHEMA_INVALID")
    step = next((item for item in plan["steps"] if item["id"] == result.get("stepId")), None)
    record = next((item for item in state["steps"] if item["id"] == result.get("stepId")), None)
    if not step or not record:
        raise ValueError("AUTO_STEP_UNKNOWN")
    if record["status"] != "READY":
        raise ValueError(f"AUTO_STEP_NOT_READY: {record['status']}")
    if result.get("skill") != step["skill"] or result.get("invocation") != step["invocation"]:
        raise ValueError("AUTO_STEP_DELEGATION_MISMATCH")
    record["attempts"] += 1
    if result.get("status") != "SUCCEEDED":
        failure_code = result.get("failureCode", "AUTO_DELEGATED_SKILL_FAILED")
        blockers = result.get("blockers", [{"code": failure_code}])
        max_attempts = step["failurePolicy"]["maxAttempts"]
        stale_fix = step["skill"] == "fix" and failure_code in {"STALE_CHECK_REPORT", "AUTO_STALE_CHECK_REPORT"}
        if stale_fix and record["attempts"] < max_attempts:
            prerequisite_id = step.get("dependsOn", [None])[-1]
            prerequisite = next((item for item in state["steps"] if item["id"] == prerequisite_id), None)
            if prerequisite:
                prerequisite.update({"status": "PENDING", "artifacts": [], "validationEvidence": [], "blockers": []})
            record.update({"status": "PENDING", "artifacts": [], "validationEvidence": [], "blockers": []})
            state["replanHistory"].append({"at": now(), "stepId": step["id"], "status": "REPLAN", "reason": "refresh-check-before-fix"})
        elif failure_code in {"SOURCE_INCOMPLETE", "BLOCKED_BY_SOURCE", "AUTO_SOURCE_REQUIRED"}:
            record["status"] = "BLOCKED"
            record["blockers"] = blockers
            state["replanHistory"].append({"at": now(), "stepId": step["id"], "status": "BLOCKED", "reason": blockers})
        elif record["attempts"] < max_attempts:
            record["status"] = "PENDING"
            record["blockers"] = blockers
            state["replanHistory"].append({"at": now(), "stepId": step["id"], "status": "RETRY", "reason": blockers})
        else:
            record["status"] = "FAILED"
            record["blockers"] = blockers
            state["replanHistory"].append({"at": now(), "stepId": step["id"], "status": "FAILED", "reason": blockers})
    else:
        record["artifacts"] = _artifact_evidence(workspace, result.get("outputArtifacts", []))
        record["validationEvidence"] = _run_validators(result.get("validatorCommands", []), workspace)
        record["status"] = "SUCCEEDED"
        record["blockers"] = []
    state = refresh_state(plan, state, workspace)
    state_path.write_text(canonical_json(state), encoding="utf-8")
    return state


def explain(plan: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    state_by_id = {item["id"]: item for item in state["steps"]}
    return {"runId": plan["runId"], "status": state["status"], "steps": [{"id": step["id"], "skill": step["skill"], "status": state_by_id[step["id"]]["status"], "dependsOn": step["dependsOn"], "authorization": step["requiredAuthorization"], "purpose": step["purpose"]} for step in plan["steps"]]}
