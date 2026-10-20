from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugin"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from validate_plugin_structure import validate_plugin  # noqa: E402


class PluginStructureTests(unittest.TestCase):
    def test_registry_metadata_and_help_index_are_consistent(self) -> None:
        self.assertEqual(validate_plugin(PLUGIN_ROOT), [])


if __name__ == "__main__":
    unittest.main()
