import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_content_package.py"
SPEC = importlib.util.spec_from_file_location("validate_content_package", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class WeChatChannelsCopyTests(unittest.TestCase):
    def validate(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "publish-copy.md"
            path.write_text(text, encoding="utf-8")
            return MODULE.validate_wechat_channels_copy(path)

    def test_accepts_exactly_five_topics(self):
        errors = self.validate(
            "# 视频号发布文案\n\n画面为AI生成。\n\n"
            "#广州 #广州塔 #城市夜读 #认真生活 #晚归的人\n"
        )
        self.assertEqual(errors, [])

    def test_rejects_six_topics(self):
        errors = self.validate(
            "# 视频号发布文案\n\n画面为AI生成。\n\n"
            "#广州 #广州塔 #城市夜读 #认真生活 #晚归的人 #珠江夜景\n"
        )
        self.assertTrue(any("exactly 5" in error for error in errors))

    def test_rejects_duplicate_topics(self):
        errors = self.validate(
            "# 视频号发布文案\n\n画面为AI生成。\n\n"
            "#广州 #广州 #城市夜读 #认真生活 #晚归的人\n"
        )
        self.assertTrue(any("duplicate" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
