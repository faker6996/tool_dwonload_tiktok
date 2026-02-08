import os
import shutil
import tempfile
import unittest
import sys
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ui.panels.media_pool import MediaPool


app = QApplication.instance() or QApplication(sys.argv)


class TestMediaPoolStockImport(unittest.TestCase):
    def setUp(self):
        self.temp_home = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_home, ignore_errors=True)

    def test_build_stock_destination_uses_media_extension(self):
        with patch.dict(os.environ, {"HOME": self.temp_home}):
            pool = MediaPool()
            stock_item = {
                "id": "pexels_123",
                "title": "Ocean Waves",
                "url": "https://cdn.example/video.mp4?token=abc",
            }
            destination = pool._build_stock_destination(stock_item)

        self.assertTrue(destination.endswith(".mp4"))
        self.assertIn("pexels_123", os.path.basename(destination))

    def test_on_stock_download_finished_imports_media(self):
        pool = MediaPool()
        with patch.object(pool, "import_media") as import_media_mock:
            pool.on_stock_download_finished(True, "/tmp/stock_file.mp4", {"id": "x"})
        import_media_mock.assert_called_once_with(["/tmp/stock_file.mp4"])

    def test_download_stock_item_uses_cached_file_without_thread(self):
        with patch.dict(os.environ, {"HOME": self.temp_home}):
            pool = MediaPool()
            stock_item = {
                "id": "pexels_42",
                "title": "City",
                "url": "https://cdn.example/city.mp4",
            }
            cached_path = pool._build_stock_destination(stock_item)
            os.makedirs(os.path.dirname(cached_path), exist_ok=True)
            with open(cached_path, "wb") as cached_file:
                cached_file.write(b"cached")

            with patch.object(pool, "import_media") as import_media_mock:
                with patch("src.ui.panels.media_pool.StockDownloadThread") as thread_mock:
                    pool.download_stock_item(stock_item)

        import_media_mock.assert_called_once_with([cached_path])
        thread_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
