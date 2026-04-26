import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.timeline.clip import Clip
from src.core.timeline.rust_adapter import (
    NativeMagneticTimeline,
    is_rust_timeline_available,
)
from src.core.timeline.track import MagneticTrack


@unittest.skipUnless(is_rust_timeline_available(), "video_core native extension unavailable")
class TestRustTimelineAdapter(unittest.TestCase):
    def test_adapter_adds_and_ripples_python_clip_objects(self):
        adapter = NativeMagneticTimeline("Test Track")
        clips = [Clip("c1", "Clip 1", duration=5.0)]
        clip2 = Clip("c2", "Clip 2", duration=3.0)

        self.assertTrue(adapter.add_clip(clips, clip2))

        self.assertEqual(clips, [clips[0], clip2])
        self.assertAlmostEqual(clips[0].start_time, 0.0)
        self.assertAlmostEqual(clips[1].start_time, 5.0)

    def test_adapter_split_creates_python_right_clip(self):
        adapter = NativeMagneticTimeline("Test Track")
        clips = [Clip("c1", "Clip 1", duration=10.0)]

        right = adapter.split_clip(clips, clips[0].id, 4.0)

        self.assertIsNotNone(right)
        self.assertEqual(len(clips), 2)
        self.assertIs(clips[1], right)
        self.assertAlmostEqual(clips[0].out_point, 4.0)
        self.assertAlmostEqual(right.start_time, 4.0)
        self.assertAlmostEqual(right.in_point, 4.0)
        self.assertAlmostEqual(right.out_point, 10.0)

    def test_magnetic_track_uses_rust_adapter_when_available(self):
        track = MagneticTrack("Test Track")
        clip1 = Clip("c1", "Clip 1", duration=5.0)
        clip2 = Clip("c2", "Clip 2", duration=3.0)

        self.assertIsNotNone(track._native_timeline)
        self.assertTrue(track.add_clip(clip1))
        self.assertTrue(track.add_clip(clip2))

        self.assertAlmostEqual(track.clips[1].start_time, 5.0)
        self.assertIs(track.remove_clip(clip1.id), clip1)
        self.assertAlmostEqual(track.clips[0].start_time, 0.0)


if __name__ == "__main__":
    unittest.main()
