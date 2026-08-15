import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTest(unittest.TestCase):
    def test_tracked_password_is_empty(self):
        setting = (ROOT / "LinkerHand/config/setting.yaml").read_text(encoding="utf-8")
        match = re.search(r"(?m)^PASSWORD:\s*([^#\n]*)", setting)
        self.assertIsNotNone(match)
        self.assertIn(match.group(1).strip(), {"", "''", '\"\"'})

    def test_runtime_uses_opt_in_environment_contract(self):
        source = (ROOT / "LinkerHand/utils/open_can.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.get("LINKERHAND_SUDO_PASSWORD", "")', source)
        self.assertNotIn('load_setting_yaml()["PASSWORD"]', source)

    def test_wrapper_identity_preserves_import_names(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# linkerhand_wrapper\n"))
        self.assertTrue((ROOT / "LinkerHand/__init__.py").is_file())
        self.assertTrue((ROOT / "linker_hand_l6.py").is_file())


if __name__ == "__main__":
    unittest.main()
