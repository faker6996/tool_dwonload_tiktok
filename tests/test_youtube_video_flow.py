import os
import sys
import unittest
from unittest.mock import ANY, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.manager import DownloaderManager
from src.core.platforms.generic import GenericDownloader
from src.ui.threads import DownloaderThread


class TestYoutubeVideoFlow(unittest.TestCase):
    def test_manager_normalizes_youtube_watch_url(self):
        manager = DownloaderManager()
        normalized = manager.normalize_youtube_url(
            "https://www.youtube.com/watch?v=GJe2S_sxY1c&list=RDGJe2S_sxY1c&start_radio=1"
        )
        self.assertEqual(normalized, "https://www.youtube.com/watch?v=GJe2S_sxY1c")

    def test_downloader_thread_uses_source_url_for_youtube_video(self):
        thread = DownloaderThread(
            url="https://rr.googlevideo.com/videoplayback?...",
            filename="/tmp/test.mp4",
            platform="youtube",
            source_path=None,
            cookies=None,
            download_mode="video",
            source_url="https://www.youtube.com/watch?v=abc123",
        )
        with patch.object(thread.downloader, "download_video", return_value=True) as download_mock:
            thread.run()
        download_mock.assert_called_once_with(
            "https://www.youtube.com/watch?v=abc123",
            "/tmp/test.mp4",
            "youtube",
            None,
            progress_callback=ANY,
        )

    def test_generic_youtube_download_uses_ytdlp_path(self):
        downloader = GenericDownloader("youtube")
        with patch.object(downloader, "download_video_by_source", return_value=True) as source_download_mock:
            ok = downloader.download("https://www.youtube.com/watch?v=abc123", "/tmp/out.mp4")
        self.assertTrue(ok)
        source_download_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
