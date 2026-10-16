"""Validate a confirmed or pending relearn reset manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any


STATES = {"WAITING_FOR_USER_CONFIRMATION", "CONFIRMED", "APPLIED", "BLOCKED"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = PurePosixPath(value.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts and "." not in path.parts


def _is_parent(parent: str, child: str) -> bool:
    parent_parts = PurePosixPath(parent).parts
    child_parts = PurePosixPath(child).parts
    return len(parent_parts) <= len(child_parts) and child_parts[: len(parent_parts)] == parent_parts


def validate_manifest(manifest: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    if manifest.get("schemaVersion") != "relearn-reset.v1":
        errors.append("schemaVersion must be relearn-reset.v1")
    if manifest.get("action") != "relearn":
        errors.append("action must be relearn")
    if manifest.get("state") not in STATES:
        errors.append("state is invalid")
    subject = manifest.get("subject")
    if not isinstance(subject, dict) or not _text(subject.get("id")) or not _relative_path(subject.get("root")):
        errors.append("subject.id and safe relative subject.root are required")
    delete_paths = manifest.get("deletePaths")
    preserve_paths = manifest.get("preservePaths")
    if not isinstance(delete_paths, list) or not delete_paths:
        errors.append("deletePaths must be a non-empty list")
        delete_paths = []
    if not isinstance(preserve_paths, list) or not preserve_paths:
        errors.append("preservePaths must be a non-empty list")
        preserve_paths = []
    for name, paths in (("deletePaths", delete_paths), ("preservePaths", preserve_paths)):
        seen: set[str] = set()
        for index, value in enumerate(paths):
            if not _relative_path(value):
                errors.append(f"{name}[{index}] is not a safe relative path")
            elif value in seen:
                errors.append(f"{name}[{index}] is duplicated")
            else:
                seen.add(value)
    for delete_path in delete_paths:
        for preserve_path in preserve_paths:
            if _is_parent(delete_path, preserve_path) or _is_parent(preserve_path, delete_path):
                errors.append(f"delete/preserve overlap: {delete_path} / {preserve_path}")
    confirmation = manifest.get("confirmation")
    if not isinstance(confirmation, dict) or confirmation.get("required") is not True:
        errors.append("confirmation.required must be true")
    if manifest.get("state") in {"CONFIRMED", "APPLIED"}:
        if not isinstance(confirmation, dict) or confirmation.get("received") is not True:
            errors.append("confirmed/applied manifest requires confirmation.received=true")
        if not isinstance(confirmation, dict) or not _text(confirmation.get("confirmedAt")):
            errors.append("confirmed/applied manifest requires confirmation.confirmedAt")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a relearn reset manifest.")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_manifest(manifest)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated relearn manifest in state {manifest['state']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
