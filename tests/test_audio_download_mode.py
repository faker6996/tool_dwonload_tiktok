import os
import shutil
import tempfile
import unittest
import sys
from unittest.mock import patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.platforms.generic import GenericDownloader
from src.core.manager import DownloaderManager


class TestAudioDownloadMode(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generic_downloader_download_audio_success(self):
        target_mp3 = os.path.join(self.temp_dir, "sample.mp3")

        class FakeYDL:
            def __init__(self, opts):
                self.opts = opts

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def download(self, urls):
                outtmpl = self.opts["outtmpl"]
                output_path = outtmpl.replace("%(ext)s", "mp3")
                with open(output_path, "wb") as output_file:
                    output_file.write(b"mp3-bytes")

        downloader = GenericDownloader("youtube")
        with patch("src.core.platforms.generic.yt_dlp.YoutubeDL", FakeYDL):
            ok = downloader.download_audio("https://youtube.com/watch?v=abc", target_mp3)

        self.assertTrue(ok)
        self.assertTrue(os.path.exists(target_mp3))

    def test_manager_delegates_download_audio(self):
        manager = DownloaderManager()
        with patch.object(manager.youtube_downloader, "download_audio", return_value=True) as audio_mock:
            ok = manager.download_audio(
                "https://youtube.com/watch?v=abc",
                "/tmp/out.mp3",
                "youtube",
                None,
                None,
            )

        self.assertTrue(ok)
        audio_mock.assert_called_once_with("https://youtube.com/watch?v=abc", "/tmp/out.mp3", None, None)


if __name__ == "__main__":
    unittest.main()
