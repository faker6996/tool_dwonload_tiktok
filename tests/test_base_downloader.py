import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.base import BaseDownloader


class _DummyDownloader(BaseDownloader):
    def extract_info(self, url):
        return {"status": "success", "url": url, "platform": "dummy"}


class _MockResponse:
    def __init__(self, status_code=200, chunks=None):
        self.status_code = status_code
        self._chunks = chunks or [b"chunk-1", b"chunk-2"]

    def iter_content(self, chunk_size=8192):
        return iter(self._chunks)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestBaseDownloader(unittest.TestCase):
    def setUp(self):
        self.downloader = _DummyDownloader()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = os.path.join(self.temp_dir.name, "video.mp4")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("requests.get")
    def test_download_success_writes_file(self, mock_get):
        mock_get.return_value = _MockResponse(status_code=200, chunks=[b"a", b"b"])

        result = self.downloader.download("https://example.com/video.mp4", self.output_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, "rb") as file_obj:
            self.assertEqual(file_obj.read(), b"ab")

    @patch("requests.get")
    def test_download_http_error_returns_false(self, mock_get):
        mock_get.return_value = _MockResponse(status_code=404, chunks=[b"err"])

        result = self.downloader.download("https://example.com/missing.mp4", self.output_path)

        self.assertFalse(result)
        self.assertFalse(os.path.exists(self.output_path))

    @patch("requests.get", side_effect=OSError("network error"))
    def test_download_exception_returns_false(self, mock_get):
        result = self.downloader.download("https://example.com/video.mp4", self.output_path)
        self.assertFalse(result)
        self.assertFalse(os.path.exists(self.output_path))


if __name__ == "__main__":
    unittest.main()
