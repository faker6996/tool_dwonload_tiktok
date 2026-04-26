import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.export.input_plan import build_input_asset_plan
from src.core.export.planner import (
    ExportAudioPlan,
    ExportClipPlan,
    ExportPlan,
    ExportPlanSettings,
    ExportStickerPlan,
    ExportSubtitlePlan,
)
from src.core.export.subtitle_asset import create_ass_subtitle_file, format_ass_time


class TestExportInputPlan(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.video_path = os.path.join(self.temp_dir, "video.mp4")
        self.audio_path = os.path.join(self.temp_dir, "voice.mp3")
        with open(self.video_path, "wb") as video_file:
            video_file.write(b"")
        with open(self.audio_path, "wb") as audio_file:
            audio_file.write(b"")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_builds_concat_and_audio_inputs(self):
        plan = ExportPlan(
            clips=[
                ExportClipPlan(
                    path=self.video_path,
                    start=0.0,
                    in_point=0.5,
                    out_point=2.0,
                    duration=1.5,
                )
            ],
            settings=ExportPlanSettings(resolution="1280x720"),
            audio_tracks=[ExportAudioPlan(path=self.audio_path)],
            total_duration=1.5,
        )

        input_plan = build_input_asset_plan(plan, "__missing_ffmpeg__")

        self.assertEqual(input_plan.render_size, (1280, 720))
        self.assertEqual(input_plan.additional_input_args, ["-i", self.audio_path])
        self.assertEqual(input_plan.audio_input_count, 1)
        self.assertFalse(input_plan.has_source_audio)
        with open(input_plan.concat_path, "r", encoding="utf-8") as concat_file:
            concat_text = concat_file.read()
        self.assertIn("file '", concat_text)
        self.assertIn("inpoint 0.500000", concat_text)
        self.assertIn("outpoint 2.000000", concat_text)
        os.remove(input_plan.concat_path)

    def test_builds_subtitle_filter_and_temp_file(self):
        plan = ExportPlan(
            clips=[
                ExportClipPlan(
                    path=self.video_path,
                    start=0.0,
                    in_point=0.0,
                    out_point=None,
                    duration=2.0,
                )
            ],
            settings=ExportPlanSettings(resolution="original"),
            subtitles=[
                ExportSubtitlePlan(
                    start_time=1.0,
                    duration=2.0,
                    text_content="hello\nworld",
                )
            ],
            total_duration=2.0,
        )

        input_plan = build_input_asset_plan(plan, "__missing_ffmpeg__")

        self.assertEqual(input_plan.render_size, (1920, 1080))
        self.assertEqual(len(input_plan.video_filters), 1)
        self.assertIn("subtitles=", input_plan.video_filters[0])
        self.assertEqual(len(input_plan.temp_files), 1)
        with open(input_plan.temp_files[0], "r", encoding="utf-8") as subtitle_file:
            subtitle_text = subtitle_file.read()
        self.assertIn("hello\\Nworld", subtitle_text)
        os.remove(input_plan.concat_path)
        os.remove(input_plan.temp_files[0])

    def test_format_ass_time(self):
        self.assertEqual(format_ass_time(3723.45), "1:02:03.45")

    def test_create_ass_subtitle_file_ignores_empty_text(self):
        subtitle_path = create_ass_subtitle_file(
            [ExportSubtitlePlan(start_time=0.0, duration=1.0, text_content="")],
            1920,
            1080,
        )

        self.assertIsNone(subtitle_path)

    def test_builds_sticker_input_when_pillow_is_available(self):
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("Pillow is not installed")

        plan = ExportPlan(
            clips=[
                ExportClipPlan(
                    path=self.video_path,
                    start=0.0,
                    in_point=0.0,
                    out_point=None,
                    duration=2.0,
                )
            ],
            settings=ExportPlanSettings(resolution="200x100"),
            stickers=[ExportStickerPlan(content="A", x=0.0, y=0.0, scale=0.5)],
            total_duration=2.0,
        )

        input_plan = build_input_asset_plan(plan, "__missing_ffmpeg__")

        self.assertEqual(input_plan.sticker_input_count, 1)
        self.assertEqual(len(input_plan.additional_input_args), 2)
        self.assertEqual(input_plan.sticker_overlays, [(50, 0)])
        os.remove(input_plan.concat_path)
        for temp_file in input_plan.temp_files:
            os.remove(temp_file)


if __name__ == "__main__":
    unittest.main()
