import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.export.planner import build_export_plan


class TestExportPlanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.clip_a = os.path.join(self.temp_dir, "a.mp4")
        self.clip_b = os.path.join(self.temp_dir, "b.mp4")
        with open(self.clip_a, "wb") as file:
            file.write(b"")
        with open(self.clip_b, "wb") as file:
            file.write(b"")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_export_plan_orders_and_normalizes_clips(self):
        plan = build_export_plan(
            [
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
            ],
            {"resolution": "original", "fps": "original", "speed": 2.0},
        )

        self.assertEqual(len(plan.clips), 2)
        self.assertTrue(plan.clips[0].path.endswith("a.mp4"))
        self.assertTrue(plan.clips[1].path.endswith("b.mp4"))
        self.assertAlmostEqual(plan.clips[0].in_point, 0.25)
        self.assertAlmostEqual(plan.clips[0].out_point, 4.0)
        self.assertAlmostEqual(plan.clips[1].out_point, 3.0)
        self.assertEqual(plan.settings.resolution, "original")
        self.assertEqual(plan.settings.fps, "original")
        self.assertAlmostEqual(plan.settings.speed, 2.0)
        self.assertEqual(plan.settings.gap_policy, "omit")
        self.assertAlmostEqual(plan.total_duration, 2.875)
        self.assertEqual(len(plan.gaps), 1)
        self.assertEqual(plan.gaps[0].policy, "omit")
        self.assertAlmostEqual(plan.gaps[0].start, 3.75)
        self.assertAlmostEqual(plan.gaps[0].duration, 6.25)
        self.assertTrue(any("Timeline gap omitted" in warning for warning in plan.warnings))

    def test_build_export_plan_rejects_timeline_gap_when_requested(self):
        with self.assertRaisesRegex(ValueError, "Timeline gap rejected"):
            build_export_plan(
                [
                    {"path": self.clip_a, "start": 0.0, "duration": 1.0},
                    {"path": self.clip_b, "start": 3.0, "duration": 1.0},
                ],
                {"gap_policy": "reject"},
            )

    def test_build_export_plan_rejects_when_no_valid_clip_exists(self):
        with self.assertRaisesRegex(ValueError, "No valid clip files to render"):
            build_export_plan(
                [
                    {"path": "", "start": 0.0, "duration": 1.0},
                    {"path": "/definitely/missing.mp4", "start": 1.0, "duration": 1.0},
                ],
                {},
            )

    def test_build_export_plan_normalizes_overlays_and_audio(self):
        audio_path = os.path.join(self.temp_dir, "voice.mp3")
        with open(audio_path, "wb") as file:
            file.write(b"")

        plan = build_export_plan(
            [{"path": self.clip_a, "start": 0.0, "duration": 5.0}],
            {"speed": 1.5},
            stickers=[{"content": "🔥", "x": 12, "y": -4, "scale": -1}],
            subtitles=[
                {"start_time": 1.0, "duration": 2.0, "text_content": "Hello"},
                {"start_time": 2.0, "duration": 2.0, "text_content": ""},
            ],
            audio_tracks=[
                {"path": audio_path, "start_time": 0.5, "duration": 3.0},
                {"path": "/missing/voice.mp3", "start_time": 0.0, "duration": 1.0},
            ],
        )

        self.assertEqual(len(plan.stickers), 1)
        self.assertAlmostEqual(plan.stickers[0].scale, 0.01)
        self.assertEqual(len(plan.subtitles), 1)
        self.assertEqual(len(plan.audio_tracks), 1)
        self.assertTrue(plan.filters.needs_filter_complex)
        self.assertTrue(plan.filters.has_video_speed_filter)
        self.assertTrue(plan.filters.has_audio_speed_filter)
        self.assertTrue(plan.filters.has_subtitles)
        self.assertEqual(plan.filters.sticker_count, 1)
        self.assertEqual(plan.filters.audio_track_count, 1)
        self.assertTrue(plan.has_filter_step("video", "subtitles"))
        self.assertTrue(plan.has_filter_step("video", "setpts"))
        self.assertTrue(plan.has_filter_step("video", "overlay"))
        self.assertTrue(plan.has_filter_step("audio", "mix"))
        self.assertTrue(plan.has_filter_step("audio", "atempo"))
        self.assertTrue(any("empty text" in warning for warning in plan.warnings))
        self.assertTrue(
            any("missing audio track path" in warning for warning in plan.warnings)
        )


if __name__ == "__main__":
    unittest.main()
