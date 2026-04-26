import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.export.filter_graph import build_filter_graph
from src.core.export.planner import (
    ExportFilterStep,
    ExportPlan,
    ExportPlanSettings,
)


class TestExportFilterGraph(unittest.TestCase):
    def test_builds_video_speed_filter_without_audio_source(self):
        plan = ExportPlan(
            clips=[],
            settings=ExportPlanSettings(speed=1.5),
            total_duration=0.0,
            filter_steps=[
                ExportFilterStep("video", "setpts", {"speed": 1.5}),
                ExportFilterStep("audio", "atempo", {"speed": 1.5}),
            ],
        )

        graph = build_filter_graph(
            export_plan=plan,
            video_filters=[],
            sticker_overlays=[],
            sticker_input_count=0,
            audio_input_count=0,
            has_source_audio=False,
        )

        self.assertTrue(graph.needs_filter_complex)
        self.assertEqual(graph.filter_complex, "[0:v]setpts=PTS/1.5[v0]")
        self.assertEqual(graph.map_args, ["-map", "[v0]", "-map", "0:a?"])

    def test_builds_overlays_audio_mix_and_audio_speed(self):
        plan = ExportPlan(
            clips=[],
            settings=ExportPlanSettings(speed=2.0),
            total_duration=0.0,
            filter_steps=[
                ExportFilterStep("video", "subtitles", {"count": 1}),
                ExportFilterStep("video", "setpts", {"speed": 2.0}),
                ExportFilterStep("video", "overlay", {"count": 2}),
                ExportFilterStep("audio", "mix", {"count": 1}),
                ExportFilterStep("audio", "atempo", {"speed": 2.0}),
            ],
        )

        graph = build_filter_graph(
            export_plan=plan,
            video_filters=["subtitles='subs.ass'"],
            sticker_overlays=[(10, 20), (30, 40)],
            sticker_input_count=2,
            audio_input_count=1,
            has_source_audio=True,
        )

        self.assertTrue(graph.needs_filter_complex)
        self.assertIn("[0:v]subtitles='subs.ass',setpts=PTS/2[v0]", graph.filter_complex)
        self.assertIn("[v0][1:v]overlay=10:20[v1]", graph.filter_complex)
        self.assertIn("[v1][2:v]overlay=30:40[v2]", graph.filter_complex)
        self.assertIn("[0:a]volume=0.5[orig]", graph.filter_complex)
        self.assertIn("[orig][3:a]amix=inputs=2:duration=longest[aout]", graph.filter_complex)
        self.assertIn("[aout]atempo=2[aout_speed]", graph.filter_complex)
        self.assertEqual(graph.map_args, ["-map", "[v2]", "-map", "[aout_speed]"])


if __name__ == "__main__":
    unittest.main()
