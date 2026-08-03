import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "create_jianying_draft.py"
SPEC = importlib.util.spec_from_file_location("create_jianying_draft", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class DraftCompatibilityTests(unittest.TestCase):
    def test_macos_auto_always_uses_modern_format(self):
        with tempfile.TemporaryDirectory() as temp:
            old = Path(temp) / "old"
            old.mkdir()
            (old / "draft_content.json").write_text("{}", encoding="utf-8")
            self.assertEqual(
                MODULE.resolve_draft_format(Path(temp), "macos", "auto"),
                "modern",
            )

    def test_windows_auto_uses_existing_modern_sample(self):
        with tempfile.TemporaryDirectory() as temp:
            current = Path(temp) / "current"
            current.mkdir()
            (current / "draft_info.json").write_text("{}", encoding="utf-8")
            self.assertEqual(
                MODULE.resolve_draft_format(Path(temp), "windows", "auto"),
                "modern",
            )

    def test_windows_without_samples_keeps_legacy_default(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(
                MODULE.resolve_draft_format(Path(temp), "windows", "auto"),
                "legacy",
            )

    def test_windows_title_rejects_ascii_pipe(self):
        with self.assertRaises(ValueError):
            MODULE.validate_title("广州夜读|测试", "windows")


if __name__ == "__main__":
    unittest.main()

