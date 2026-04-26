import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.export.command_plan import build_output_command_plan
from src.core.export.planner import ExportPlan, ExportPlanSettings


class TestExportCommandPlan(unittest.TestCase):
    def test_keeps_original_resolution_and_fps(self):
        plan = ExportPlan(
            clips=[],
            settings=ExportPlanSettings(resolution="original", fps="original"),
            total_duration=0.0,
        )

        command_plan = build_output_command_plan(plan)

        self.assertEqual(command_plan.size_args, [])
        self.assertEqual(command_plan.fps_args, [])

    def test_builds_default_encoding_options(self):
        plan = ExportPlan(
            clips=[],
            settings=ExportPlanSettings(resolution="1280x720", fps=60),
            total_duration=0.0,
        )

        command_plan = build_output_command_plan(plan)

        self.assertEqual(command_plan.size_args, ["-s", "1280x720"])
        self.assertEqual(command_plan.fps_args, ["-r", "60.0"])
        self.assertEqual(command_plan.audio_codec_args, ["-c:a", "aac", "-b:a", "192k"])
        self.assertIn("libx264", command_plan.video_codec_args)


if __name__ == "__main__":
    unittest.main()
