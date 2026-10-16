from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugin" / "skills" / "relearn"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from reset_derived_state import apply_reset, resolve_safe  # noqa: E402
from validate_relearn_manifest import validate_manifest  # noqa: E402


PLAYBOOKS = {"impact-analysis.md", "confirm-and-reset.md", "rebuild.md", "validate.md"}
REFERENCES = {"relearn-contract.md", "reset-manifest.md"}


def links_in(path: Path) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


def load_manifest() -> dict:
    return json.loads((SKILL_ROOT / "examples" / "reset-manifest.json").read_text(encoding="utf-8"))


class RelearnStructureTests(unittest.TestCase):
    def test_front_door_is_small_and_routes_playbooks(self) -> None:
        entrypoint = SKILL_ROOT / "SKILL.md"
        self.assertLessEqual(len(entrypoint.read_text(encoding="utf-8").splitlines()), 80)
        for name in PLAYBOOKS:
            self.assertTrue((SKILL_ROOT / "playbooks" / name).is_file(), name)

    def test_references_exist_and_links_resolve(self) -> None:
        for name in REFERENCES:
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)
        for document in [SKILL_ROOT / "SKILL.md"] + sorted((SKILL_ROOT / "playbooks").glob("*.md")):
            for target in links_in(document):
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue((document.parent / target).resolve().is_file(), f"{document}: {target}")

    def test_pending_manifest_requires_confirmation_before_apply(self) -> None:
        manifest = load_manifest()
        self.assertEqual(validate_manifest(manifest), [])
        with self.assertRaises(ValueError):
            apply_reset(manifest, True)

    def test_confirmed_reset_preserves_source_paths(self) -> None:
        manifest = copy.deepcopy(load_manifest())
        manifest["state"] = "CONFIRMED"
        manifest["confirmation"] = {"required": True, "received": True, "confirmedAt": "2026-10-16T12:00:00+08:00"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "subject" / "math-1"
            (root / "derived").mkdir(parents=True)
            (root / "sources").mkdir(parents=True)
            (root / "derived" / "card.json").write_text("derived", encoding="utf-8")
            (root / "sources" / "source.pdf").write_text("source", encoding="utf-8")
            manifest["subject"]["root"] = str(root)
            manifest["deletePaths"] = ["derived"]
            manifest["preservePaths"] = ["sources"]
            self.assertEqual(validate_manifest(manifest), [])
            apply_reset(manifest, True)
            self.assertFalse((root / "derived").exists())
            self.assertTrue((root / "sources" / "source.pdf").exists())


if __name__ == "__main__":
    unittest.main()
