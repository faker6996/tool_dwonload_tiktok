import os
import shutil
import tempfile
import unittest
import sys
from unittest.mock import patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.api.stock_api import StockAPI


class MockResponse:
    def __init__(self, payload=None, chunks=None, status_code=200, raise_error=None):
        self._payload = payload or {}
        self._chunks = chunks or []
        self.status_code = status_code
        self._raise_error = raise_error

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self._raise_error:
            raise self._raise_error

    def iter_content(self, chunk_size=1024):
        for chunk in self._chunks:
            yield chunk

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestStockAPI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_search_media_uses_mock_without_api_key(self):
        with patch.dict(os.environ, {"PEXELS_API_KEY": ""}):
            api = StockAPI()
            results = api.search_media("nature")

        self.assertEqual(len(results), 5)
        self.assertEqual(results[0]["provider"], "MockProvider")
        self.assertIn("nature", results[0]["title"].lower())

    def test_search_media_uses_pexels_when_api_key_available(self):
        payload = {
            "videos": [
                {
                    "id": 123,
                    "duration": 9,
                    "image": "https://img.example/thumb.jpg",
                    "user": {"name": "Alice"},
                    "video_files": [
                        {"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "https://cdn.example/full.mp4"},
                        {"file_type": "video/mp4", "width": 720, "height": 1280, "link": "https://cdn.example/proxy.mp4"},
                    ],
                }
            ]
        }

        with patch.dict(os.environ, {"PEXELS_API_KEY": "test-key"}):
            api = StockAPI()
            with patch("src.core.api.stock_api.requests.get", return_value=MockResponse(payload=payload)):
                results = api.search_media("travel")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["provider"], "Pexels")
        self.assertEqual(results[0]["id"], "pexels_123")
        self.assertEqual(results[0]["url"], "https://cdn.example/proxy.mp4")

    def test_download_media_success(self):
        destination = os.path.join(self.temp_dir, "stock.mp4")
        api = StockAPI()
        response = MockResponse(chunks=[b"abc", b"def"])

        with patch("src.core.api.stock_api.requests.get", return_value=response):
            result = api.download_media("id1", "https://cdn.example/v.mp4", destination)

        self.assertEqual(result, destination)
        self.assertTrue(os.path.exists(destination))
        with open(destination, "rb") as output_file:
            self.assertEqual(output_file.read(), b"abcdef")

    def test_download_media_failure_returns_empty(self):
        destination = os.path.join(self.temp_dir, "stock.mp4")
        api = StockAPI()

        with patch(
            "src.core.api.stock_api.requests.get",
            side_effect=RuntimeError("network error"),
        ):
            result = api.download_media("id2", "https://cdn.example/fail.mp4", destination)

        self.assertEqual(result, "")
        self.assertFalse(os.path.exists(destination))


if __name__ == "__main__":
    unittest.main()
