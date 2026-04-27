import unittest
import os
import sys
import tempfile
from unittest import mock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.ingestion import MediaIngestion

class TestIngestion(unittest.TestCase):
    def setUp(self):
        self.ingestion = MediaIngestion()
        
    def test_probe_non_existent_file(self):
        result = self.ingestion.probe_file("non_existent.mp4")
        self.assertIsNone(result)

    def test_thumbnail_generation_falls_back_without_known_duration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.ingestion.cache_dir = temp_dir
            video_path = os.path.join(temp_dir, "short.mp4")
            with open(video_path, "wb") as video_file:
                video_file.write(b"video")

            first_failure = subprocess_error()
            with mock.patch(
                "src.core.ingestion.subprocess.run",
                side_effect=[first_failure, None],
            ) as run_mock:
                thumbnail_path = self.ingestion._generate_thumbnail(video_path)

        self.assertTrue(thumbnail_path.endswith(".jpg"))
        self.assertEqual(run_mock.call_count, 2)
        self.assertIn("00:00:00.100", run_mock.call_args_list[0].args[0])
        self.assertIn("00:00:00.000", run_mock.call_args_list[1].args[0])

    def test_thumbnail_generation_uses_safe_seek_for_known_short_duration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.ingestion.cache_dir = temp_dir
            video_path = os.path.join(temp_dir, "short.mp4")
            with open(video_path, "wb") as video_file:
                video_file.write(b"video")

            with mock.patch("src.core.ingestion.subprocess.run", return_value=None) as run_mock:
                thumbnail_path = self.ingestion._generate_thumbnail(video_path, duration=2.0)

        self.assertTrue(thumbnail_path.endswith(".jpg"))
        self.assertEqual(run_mock.call_count, 1)
        self.assertIn("00:00:00.500", run_mock.call_args.args[0])

    # We can't easily test a real file without having one. 
    # But we can check if the class instantiates and methods exist.


def subprocess_error():
    import subprocess

    return subprocess.CalledProcessError(234, ["ffmpeg"])

if __name__ == '__main__':
    unittest.main()
