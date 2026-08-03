import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "align_jianying_voice.py"
SPEC = importlib.util.spec_from_file_location("align_jianying_voice", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class VoiceAlignmentTests(unittest.TestCase):
    def test_retime_scales_every_boundary_and_closes_exactly(self):
        timeline = {
            "duration": 10.0,
            "items": [
                {"start": 0.0, "end": 4.0, "text": "甲"},
                {"start": 4.0, "end": 10.0, "text": "乙"},
            ],
        }
        result = MODULE.retime_timeline(timeline, 12.5)
        self.assertEqual(result["items"][0]["end"], 5.0)
        self.assertEqual(result["items"][1]["start"], 5.0)
        self.assertEqual(result["items"][1]["end"], 12.5)

    def test_rejects_multiple_text_readings(self):
        with tempfile.TemporaryDirectory() as temp:
            reading = Path(temp) / "textReading"
            reading.mkdir()
            (reading / "one.wav").write_bytes(b"one")
            (reading / "two.wav").write_bytes(b"two")
            with self.assertRaisesRegex(RuntimeError, "实际检测到 2 段"):
                MODULE.find_single_reading(Path(temp))

    def test_accepts_one_text_reading(self):
        with tempfile.TemporaryDirectory() as temp:
            reading = Path(temp) / "textReading"
            reading.mkdir()
            expected = reading / "one.wav"
            expected.write_bytes(b"one")
            self.assertEqual(MODULE.find_single_reading(Path(temp)), expected)


if __name__ == "__main__":
    unittest.main()
