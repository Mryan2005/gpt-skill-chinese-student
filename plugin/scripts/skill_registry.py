"""Shared skill registry and deterministic command-routing primitives."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REGISTRY_RELATIVE_PATH = Path("references") / "skill-registry.v1.json"
ROUTE_RESULT_VERSION = "command-route.v1"
VISIBLE_KIND = "workflow"
INTERNAL_KIND = "domain-model"


def load_registry(plugin_root: Path) -> dict[str, Any]:
    path = plugin_root / REGISTRY_RELATIVE_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _compact(value: str) -> str:
    """Normalize punctuation and whitespace while retaining Chinese words."""

    return re.sub(r"[\W_]+", "", value.casefold(), flags=re.UNICODE)


def _matches(text: str, values: list[str]) -> list[str]:
    return [value for value in values if _compact(value) and _compact(value) in text]


def _score_route(text: str, route: dict[str, Any]) -> tuple[int, list[str]]:
    matched_phrases = _matches(text, route.get("phrases", []))
    matched_terms = _matches(text, route.get("terms", []))
    score = int(route.get("priority", 0)) if matched_phrases or matched_terms else 0
    signals: list[str] = []
    for phrase in matched_phrases:
        score += 50 + min(len(_compact(phrase)), 30)
        signals.append(f"phrase:{phrase}")
    for term in matched_terms:
        score += 8
        signals.append(f"term:{term}")
    for phrase in _matches(text, route.get("excludePhrases", [])):
        score -= 40
        signals.append(f"exclude:{phrase}")
    return score, signals


def _best_subroute(text: str, entry: dict[str, Any]) -> str | None:
    routes = entry.get("subcommandRoutes", [])
    ranked: list[tuple[int, str]] = []
    for route in routes:
        score = 0
        for phrase in _matches(text, route.get("phrases", [])):
            score += 50 + len(_compact(phrase))
        score += 8 * len(_matches(text, route.get("terms", [])))
        if score:
            ranked.append((score, str(route["id"])))
    if not ranked:
        return entry.get("defaultSubcommand")
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def _best_playbook(text: str, entry: dict[str, Any]) -> str | None:
    ranked: list[tuple[int, str]] = []
    for route in entry.get("playbooks", []):
        score = sum(50 + len(_compact(phrase)) for phrase in _matches(text, route.get("phrases", [])))
        if score:
            ranked.append((score, str(route["id"])))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def _best_domain(text: str, registry: dict[str, Any], subject: str | None = None) -> str | None:
    haystack = _compact(" ".join(value for value in (text, subject or "") if value))
    ranked: list[tuple[int, str]] = []
    for domain in registry.get("domains", []):
        score = int(domain.get("priority", 0))
        score += sum(50 + len(_compact(phrase)) for phrase in _matches(haystack, domain.get("phrases", [])))
        if score > int(domain.get("priority", 0)):
            ranked.append((score, str(domain["id"])))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1]))
    if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
        return None
    return ranked[0][1]


def _explicit_command(text: str, command_ids: set[str]) -> tuple[str | None, str | None]:
    namespaced = re.match(r"^\s*\$?chinese[\s-]*student\s*:\s*([a-z][a-z0-9-]*)\b", text.casefold())
    if namespaced and namespaced.group(1) in command_ids:
        return namespaced.group(1), "namespaced-command"
    bare = re.match(r"^\s*\$?([a-z][a-z0-9-]*)\b(?:\s|$)", text.casefold())
    if bare and bare.group(1) in command_ids:
        return bare.group(1), "bare-command"
    return None, None


def _canonical(command: str | None, registry: dict[str, Any]) -> str | None:
    if command is None:
        return None
    prefix = registry["plugin"]["combinedInvocationPrefix"]
    return f"{prefix}{command}"


def route_command(text: str, *, registry: dict[str, Any], subject: str | None = None) -> dict[str, Any]:
    """Return a read-only route plan; this function never invokes a skill."""

    if not _text(text):
        raise ValueError("text must be non-empty")
    commands = [entry for entry in registry.get("commands", []) if entry.get("visibility") == "user"]
    all_entries = {str(entry["id"]): entry for entry in registry.get("commands", [])}
    command_ids = set(all_entries)

    explicit, explicit_kind = _explicit_command(text, command_ids)
    domain = _best_domain(text, registry, subject)
    if explicit:
        entry = all_entries[explicit]
        if entry.get("visibility") == "internal":
            return {
                "schemaVersion": ROUTE_RESULT_VERSION,
                "input": text,
                "command": registry["defaultCommand"],
                "canonicalInvocation": _canonical(registry["defaultCommand"], registry),
                "subcommand": None,
                "playbook": None,
                "domainModel": explicit,
                "confidence": "high",
                "requiresClarification": False,
                "candidates": [{"command": registry["defaultCommand"], "score": 1000, "signals": ["internal-domain-model", explicit_kind]}],
                "signals": ["internal-domain-model", explicit_kind],
                "reason": f"{explicit} is a domain model and is loaded by {registry['defaultCommand']}",
            }
        return {
            "schemaVersion": ROUTE_RESULT_VERSION,
            "input": text,
            "command": explicit,
            "canonicalInvocation": _canonical(explicit, registry),
            "subcommand": _best_subroute(_compact(text), entry),
            "playbook": _best_playbook(_compact(text), entry),
            "domainModel": domain,
            "confidence": "high",
            "requiresClarification": False,
            "candidates": [{"command": explicit, "score": 1000, "signals": [explicit_kind]}],
            "signals": [explicit_kind],
            "reason": "explicit command identity",
        }

    normalized = _compact(text)
    ranked: list[tuple[int, int, str, list[str]]] = []
    for entry in commands:
        score, signals = _score_route(normalized, entry.get("route", {}))
        if score > 0:
            ranked.append((score, int(entry.get("route", {}).get("priority", 0)), str(entry["id"]), signals))
    if not ranked:
        fallback = next((entry for entry in commands if entry.get("route", {}).get("fallback")), None)
        if fallback is None:
            return {
                "schemaVersion": ROUTE_RESULT_VERSION,
                "input": text,
                "command": None,
                "canonicalInvocation": None,
                "subcommand": None,
                "playbook": None,
                "domainModel": domain,
                "confidence": "none",
                "requiresClarification": True,
                "candidates": [],
                "signals": [],
                "reason": "no workflow matched the request",
            }
        ranked = [(1, int(fallback.get("route", {}).get("priority", 0)), str(fallback["id"]), ["fallback:learn"])]

    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    candidates = [{"command": command, "score": score, "signals": signals} for score, _priority, command, signals in ranked[:5]]
    top = ranked[0]
    ambiguous = len(ranked) > 1 and ranked[1][0] >= top[0] - 8 and not any(signal.startswith("phrase:") for signal in top[3])
    command = None if ambiguous else top[2]
    entry = all_entries[top[2]] if command else None
    confidence = "ambiguous" if ambiguous else ("high" if top[0] >= 130 else "medium" if top[0] >= 80 else "low")
    signals = list(top[3])
    if domain and command:
        signals.append(f"domain:{domain}")
    return {
        "schemaVersion": ROUTE_RESULT_VERSION,
        "input": text,
        "command": command,
        "canonicalInvocation": _canonical(command, registry),
        "subcommand": _best_subroute(normalized, entry) if entry else None,
        "playbook": _best_playbook(normalized, entry) if entry else None,
        "domainModel": domain,
        "confidence": confidence,
        "requiresClarification": ambiguous,
        "candidates": candidates,
        "signals": signals,
        "reason": "multiple workflows have comparable evidence; ask one focused clarification" if ambiguous else "best matching workflow by explicit route signals",
    }


def validate_registry(registry: dict[str, Any], plugin_root: Path) -> list[str]:
    errors: list[str] = []
    if registry.get("schemaVersion") != "skill-registry.v1":
        errors.append("registry schemaVersion must be skill-registry.v1")
    plugin = registry.get("plugin")
    if not isinstance(plugin, dict) or plugin.get("id") != "chinese-student":
        errors.append("registry plugin.id must be chinese-student")
    commands = registry.get("commands")
    if not isinstance(commands, list):
        return errors + ["registry commands must be an array"]
    ids = [entry.get("id") for entry in commands if isinstance(entry, dict)]
    if any(not _text(value) for value in ids):
        errors.append("every command needs a non-empty id")
    if len(ids) != len(set(ids)):
        errors.append("command ids must be unique")
    skills_root = plugin_root / "skills"
    live = {path.name for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
    if set(ids) != live:
        errors.append(f"registry/live skill mismatch; registry-only={sorted(set(ids) - live)}; live-only={sorted(live - set(ids))}")
    for entry in commands:
        if not isinstance(entry, dict):
            continue
        command = entry.get("id")
        if not _text(command):
            continue
        expected_picker = f"{plugin['pickerDisplayPrefix']}{command}" if isinstance(plugin, dict) else ""
        expected_invocation = f"{plugin['combinedInvocationPrefix']}{command}" if isinstance(plugin, dict) else ""
        if entry.get("pickerDisplayName") != expected_picker:
            errors.append(f"{command} pickerDisplayName must be {expected_picker}")
        if entry.get("combinedInvocation") != expected_invocation:
            errors.append(f"{command} combinedInvocation must be {expected_invocation}")
        kind = entry.get("kind")
        visibility = entry.get("visibility")
        if kind == VISIBLE_KIND and visibility != "user":
            errors.append(f"workflow {command} must be user-visible")
        if kind == INTERNAL_KIND and visibility != "internal":
            errors.append(f"domain model {command} must be internal")
        if kind == INTERNAL_KIND and entry.get("loadedBy") != "learn":
            errors.append(f"domain model {command} must be loaded by learn")
        if kind == VISIBLE_KIND:
            route = entry.get("route")
            if not isinstance(route, dict):
                errors.append(f"workflow {command} needs a route object")
            elif not isinstance(route.get("priority"), int):
                errors.append(f"workflow {command} route.priority must be an integer")
    default = registry.get("defaultCommand")
    if default not in ids or next((entry for entry in commands if entry.get("id") == default), {}).get("visibility") != "user":
        errors.append("defaultCommand must name a user-visible command")
    domains = registry.get("domains", [])
    if not isinstance(domains, list):
        errors.append("domains must be an array")
    else:
        for domain in domains:
            if domain.get("id") not in ids:
                errors.append(f"domain route points to unknown skill {domain.get('id')}")
            elif next(entry for entry in commands if entry.get("id") == domain["id"]).get("kind") != INTERNAL_KIND:
                errors.append(f"domain route {domain.get('id')} must point to a domain-model skill")
    return errors


def validate_route_result(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schemaVersion") != ROUTE_RESULT_VERSION:
        errors.append("schemaVersion must be command-route.v1")
    if not _text(result.get("input")):
        errors.append("input must be non-empty")
    if result.get("confidence") not in {"high", "medium", "low", "ambiguous", "none"}:
        errors.append("confidence is invalid")
    if not isinstance(result.get("requiresClarification"), bool):
        errors.append("requiresClarification must be boolean")
    if not isinstance(result.get("candidates"), list):
        errors.append("candidates must be an array")
    if not isinstance(result.get("signals"), list):
        errors.append("signals must be an array")
    if result.get("requiresClarification") and result.get("command") is not None:
        errors.append("ambiguous routes must not select a command")
    if result.get("command") is None and result.get("canonicalInvocation") is not None:
        errors.append("null command must have null canonicalInvocation")
    return errors
