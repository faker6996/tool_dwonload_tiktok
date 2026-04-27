import json
import os
import sys
import tempfile
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.profile_analysis import (
    analyze_profile_report,
    classify_profile_event,
    format_hotspot_table,
    load_profile_report,
)


class TestProfileAnalysis(unittest.TestCase):
    def test_classifies_external_and_rust_candidate_events(self):
        self.assertEqual(
            classify_profile_event("download.video_attempt"),
            (
                "external_bound",
                False,
                "Do not port to Rust; optimize provider, FFmpeg, caching, or concurrency.",
            ),
        )
        self.assertEqual(classify_profile_event("export.render_prepare")[0], "python_cpu_candidate")
        self.assertTrue(classify_profile_event("export.render_prepare")[1])
        self.assertEqual(classify_profile_event("media_ingestion.probe_file")[0], "inspect")
        self.assertFalse(classify_profile_event("media_ingestion.probe_file")[1])
        self.assertEqual(classify_profile_event("queue.process_task")[0], "inspect")

    def test_analyze_report_sorts_and_flags_candidates(self):
        report = {
            "summary": [
                {"name": "export.render_prepare", "count": 2, "total_ms": 40, "max_ms": 30},
                {"name": "export.ffmpeg_render", "count": 1, "total_ms": 900, "avg_ms": 900, "max_ms": 900},
            ],
        }

        hotspots = analyze_profile_report(report)

        self.assertEqual(hotspots[0].name, "export.ffmpeg_render")
        self.assertFalse(hotspots[0].rust_candidate)
        self.assertEqual(hotspots[1].avg_ms, 20)
        self.assertTrue(hotspots[1].rust_candidate)

    def test_load_report_and_format_table(self):
        report = {
            "summary": [
                {"name": "media_ingestion.probe_file", "count": 1, "total_ms": 12, "max_ms": 12},
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "report.json")
            with open(path, "w", encoding="utf-8") as report_file:
                json.dump(report, report_file)

            loaded_report = load_profile_report(path)

        hotspots = analyze_profile_report(loaded_report)
        table = format_hotspot_table(hotspots)

        self.assertEqual(hotspots[0].name, "media_ingestion.probe_file")
        self.assertFalse(hotspots[0].rust_candidate)
        self.assertIn("rust", table)
        self.assertIn("media_ingestion.probe_file", table)


if __name__ == "__main__":
    unittest.main()
