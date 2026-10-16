"""Validate Source/Derived separation for a platform record envelope."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record(record: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record must be an object"]
    if record.get("schemaVersion") != "platform-subject.v1":
        errors.append("schemaVersion must be platform-subject.v1")
    for field in ("sourceVersion", "derivedVersion"):
        if not isinstance(record.get(field), int) or record[field] < 1:
            errors.append(f"{field} must be a positive integer")
    sources = record.get("sources")
    derived = record.get("derived")
    if not isinstance(sources, list) or not isinstance(derived, list):
        return errors + ["sources and derived must be lists"]

    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        path = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{path} must be an object")
            continue
        source_id = source.get("id")
        if not _text(source_id):
            errors.append(f"{path}.id is required")
        elif source_id in source_ids:
            errors.append(f"{path}.id is duplicated: {source_id}")
        else:
            source_ids.add(source_id)
        if not _text(source.get("entityType")):
            errors.append(f"{path}.entityType is required")
        if "text" not in source and "file" not in source and "content" not in source:
            errors.append(f"{path} must retain original text, file, or content")
        if source.get("mutatedByDerived") is True:
            errors.append(f"SOURCE_MUTATED_BY_DERIVATION: {path}")

    derived_ids: set[str] = set()
    for index, item in enumerate(derived):
        path = f"derived[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object")
            continue
        item_id = item.get("id")
        if not _text(item_id):
            errors.append(f"{path}.id is required")
        elif item_id in derived_ids:
            errors.append(f"{path}.id is duplicated: {item_id}")
        else:
            derived_ids.add(item_id)
        if not _text(item.get("type")):
            errors.append(f"{path}.type is required")
        refs = item.get("sourceRefs", item.get("derivedFrom"))
        if not isinstance(refs, list) or not refs:
            errors.append(f"DERIVED_WITHOUT_PROVENANCE: {path}")
            continue
        for ref_index, ref in enumerate(refs):
            ref_path = f"{path}.sourceRefs[{ref_index}]"
            if not isinstance(ref, dict) or ref.get("sourceId") not in source_ids:
                errors.append(f"{ref_path} must reference an existing sourceId")
            elif not _text(ref.get("locator")):
                errors.append(f"{ref_path}.locator is required")
        if any(key in item for key in ("sourceText", "originalText", "sourceContent")):
            errors.append(f"SOURCE_AND_DERIVED_COLLAPSED: {path}")
        if item.get("conflictsWithSource") is True and item.get("status") not in {"conflict", "needs-review"}:
            errors.append(f"DERIVED_CONFLICTS_WITH_SOURCE: {path} must be marked conflict or needs-review")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Source/Derived separation.")
    parser.add_argument("record", type=Path)
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_record(record)
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: validated {len(record['sources'])} source(s) and {len(record['derived'])} derived record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
