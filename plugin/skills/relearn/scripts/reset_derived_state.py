"""Apply a confirmed relearn reset manifest without touching preserved Source."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from validate_relearn_manifest import validate_manifest


def resolve_safe(root: Path, relative: str) -> Path:
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes subject root: {relative}")
    return target


def apply_reset(manifest: dict, apply: bool) -> list[str]:
    root = (Path(manifest["subject"]["root"]).expanduser()).resolve()
    targets = [resolve_safe(root, path) for path in manifest["deletePaths"]]
    existing = [str(path) for path in targets if path.exists()]
    if not apply:
        return existing
    if manifest["state"] != "CONFIRMED" or manifest["confirmation"].get("received") is not True:
        raise ValueError("destructive reset requires state=CONFIRMED and confirmation.received=true")
    for target in targets:
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply a confirmed relearn reset manifest.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        errors = validate_manifest(manifest)
        if errors:
            raise ValueError("; ".join(errors))
        residual = apply_reset(manifest, args.apply)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"RESET_ERROR: {exc}", file=sys.stderr)
        return 2
    if args.apply:
        print("RESET_APPLIED")
        print("DELETED_DERIVED_PATHS: []")
    else:
        print("DRY_RUN")
        print(f"EXISTING_DELETE_TARGETS: {residual}")
        print("Use --apply only after explicit confirmation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
