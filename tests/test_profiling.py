import os
import sys
import time
import json
import tempfile
import unittest
from unittest import mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.profiling import (
    ProfileCollector,
    build_profile_report,
    collector,
    emit_profile_report,
    is_profiling_enabled,
    profile_output_path,
    profile_scope,
    profile_threshold_ms,
    write_profile_report,
)


class TestProfiling(unittest.TestCase):
    def tearDown(self):
        collector.reset()

    def test_profile_scope_is_noop_when_disabled(self):
        with mock.patch.dict(os.environ, {"VIDEO_TOOL_PROFILE": "0"}, clear=False):
            collector.reset()
            with profile_scope("disabled"):
                time.sleep(0.001)

        self.assertEqual(collector.snapshot(), [])

    def test_profile_scope_records_when_enabled(self):
        with mock.patch.dict(
            os.environ,
            {"VIDEO_TOOL_PROFILE": "1", "VIDEO_TOOL_PROFILE_THRESHOLD_MS": "999999"},
            clear=False,
        ):
            collector.reset()
            with profile_scope("enabled", phase="test"):
                time.sleep(0.001)

        events = collector.snapshot()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].name, "enabled")
        self.assertEqual(events[0].metadata["phase"], "test")
        self.assertGreater(events[0].elapsed_ms, 0)

    def test_collector_summary_orders_by_total_time(self):
        local_collector = ProfileCollector()
        local_collector.record("fast", 1)
        local_collector.record("slow", 10)
        local_collector.record("fast", 2, {"last": True})

        summary = local_collector.summary()

        self.assertEqual(summary[0]["name"], "slow")
        self.assertEqual(summary[1]["name"], "fast")
        self.assertEqual(summary[1]["count"], 2)
        self.assertEqual(summary[1]["total_ms"], 3)
        self.assertEqual(summary[1]["last_metadata"], {"last": True})

    def test_env_helpers_accept_expected_values(self):
        with mock.patch.dict(
            os.environ,
            {
                "VIDEO_TOOL_PROFILING": "true",
                "VIDEO_TOOL_PROFILE_THRESHOLD_MS": "12.5",
                "VIDEO_TOOL_PROFILE_OUTPUT": "/tmp/profile.json",
            },
            clear=False,
        ):
            self.assertTrue(is_profiling_enabled())
            self.assertEqual(profile_threshold_ms(), 12.5)
            self.assertEqual(profile_output_path(), "/tmp/profile.json")

    def test_build_and_write_profile_report(self):
        collector.reset()
        collector.record("one", 5, {"path": "a.mp4"})
        collector.record("two", 10)

        report = build_profile_report()

        self.assertEqual(report["event_count"], 2)
        self.assertEqual(report["summary"][0]["name"], "two")
        self.assertEqual(report["events"][0]["metadata"], {"path": "a.mp4"})

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "profile", "report.json")
            write_profile_report(output_path)
            with open(output_path, encoding="utf-8") as report_file:
                written_report = json.load(report_file)

        self.assertEqual(written_report["event_count"], 2)
        self.assertEqual(written_report["events"][0]["name"], "one")

    def test_emit_profile_report_writes_configured_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "profile.json")
            with mock.patch.dict(
                os.environ,
                {
                    "VIDEO_TOOL_PROFILE": "1",
                    "VIDEO_TOOL_PROFILE_OUTPUT": output_path,
                    "VIDEO_TOOL_PROFILE_THRESHOLD_MS": "999999",
                },
                clear=False,
            ):
                collector.reset()
                collector.record("emit", 12)
                emit_profile_report()

            with open(output_path, encoding="utf-8") as report_file:
                report = json.load(report_file)

        self.assertEqual(report["event_count"], 1)
        self.assertEqual(report["summary"][0]["name"], "emit")


if __name__ == "__main__":
    unittest.main()
