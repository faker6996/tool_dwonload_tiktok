import os
import shutil
import tempfile
import unittest
import sys
from unittest.mock import patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.ingestion import MediaIngestion


class TestIngestionProxy(unittest.TestCase):
    def setUp(self):
        self.temp_home = tempfile.mkdtemp()
        self.source_dir = tempfile.mkdtemp()
        self.source_path = os.path.join(self.source_dir, "input.mp4")
        with open(self.source_path, "w") as source_file:
            source_file.write("source-data")

    def tearDown(self):
        shutil.rmtree(self.temp_home, ignore_errors=True)
        shutil.rmtree(self.source_dir, ignore_errors=True)

    def test_generate_proxy_uses_ffmpeg_output_when_successful(self):
        with patch.dict(os.environ, {"HOME": self.temp_home}):
            ingestion = MediaIngestion()

            def fake_run(cmd, capture_output, text, check):
                temp_output = cmd[-1]
                with open(temp_output, "w") as encoded:
                    encoded.write("encoded-proxy")
                return 0

            with patch("src.core.ingestion.subprocess.run", side_effect=fake_run):
                proxy_path = ingestion.generate_proxy(self.source_path)

            self.assertTrue(os.path.exists(proxy_path))
            self.assertTrue(proxy_path.endswith("_proxy.mp4"))
            with open(proxy_path, "r") as proxy_file:
                self.assertEqual(proxy_file.read(), "encoded-proxy")

    def test_generate_proxy_falls_back_to_copy_on_ffmpeg_error(self):
        with patch.dict(os.environ, {"HOME": self.temp_home}):
            ingestion = MediaIngestion()

            with patch(
                "src.core.ingestion.subprocess.run",
                side_effect=FileNotFoundError("ffmpeg not found"),
            ):
                proxy_path = ingestion.generate_proxy(self.source_path)

            self.assertTrue(os.path.exists(proxy_path))
            self.assertTrue(proxy_path.endswith("_proxy.mp4"))
            with open(proxy_path, "r") as proxy_file:
                self.assertEqual(proxy_file.read(), "source-data")


if __name__ == "__main__":
    unittest.main()
