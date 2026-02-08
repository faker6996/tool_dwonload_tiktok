import os
import shutil
import sys
import tempfile
import unittest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.export.renderer import render_engine


class TestExportTimelineSemantics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.clip_a = os.path.join(self.temp_dir, "a.mp4")
        self.clip_b = os.path.join(self.temp_dir, "b.mp4")
        with open(self.clip_a, "wb") as f:
            f.write(b"")
        with open(self.clip_b, "wb") as f:
            f.write(b"")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_concat_file_respects_order_and_trim(self):
        output_path = os.path.join(self.temp_dir, "out.mp4")
        render_engine.settings.update(
            {
                "resolution": "1920x1080",
                "fps": 30,
                "speed": 1.0,
            }
        )

        clips = [
            {
                "path": self.clip_b,
                "start": 10.0,
                "in_point": 1.0,
                "duration": 2.0,
            },
            {
                "path": self.clip_a,
                "start": 0.0,
                "in_point": 0.25,
                "out_point": 4.0,
                "duration": 3.5,
            },
        ]

        cmd, concat_path, temp_files = render_engine._build_ffmpeg_command(clips, output_path)
        self.assertIn("-f", cmd)
        self.assertTrue(os.path.exists(concat_path))

        with open(concat_path, "r", encoding="utf-8") as f:
            concat_text = f.read()

        self.assertLess(concat_text.index("a.mp4"), concat_text.index("b.mp4"))
        self.assertIn("inpoint 0.250000", concat_text)
        self.assertIn("outpoint 4.000000", concat_text)
        self.assertIn("inpoint 1.000000", concat_text)
        self.assertIn("outpoint 3.000000", concat_text)

        if concat_path and os.path.exists(concat_path):
            os.remove(concat_path)
        for temp_path in temp_files:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
