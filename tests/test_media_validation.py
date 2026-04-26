import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.media_validation import validate_media_file, validate_or_remove


class TestMediaValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_file(self, name: str, content: bytes) -> str:
        path = os.path.join(self.temp_dir, name)
        with open(path, "wb") as file_obj:
            file_obj.write(content)
        return path

    def test_rejects_html_saved_as_media(self):
        path = self._write_file("video.mp4", b"<!doctype html><html>Forbidden</html>")

        result = validate_media_file(path)

        self.assertFalse(result.ok)
        self.assertIn("HTML", result.reason)

    def test_rejects_text_error_saved_as_media(self):
        path = self._write_file("audio.mp3", b"ERROR: forbidden access denied")

        result = validate_media_file(path)

        self.assertFalse(result.ok)
        self.assertIn("text error", result.reason)

    def test_accepts_non_error_media_payload(self):
        path = self._write_file("audio.mp3", b"mp3-bytes")

        result = validate_media_file(path)

        self.assertTrue(result.ok)

    def test_validate_or_remove_deletes_invalid_file(self):
        path = self._write_file("video.mp4", b"<html>not found</html>")

        result = validate_or_remove(path)

        self.assertFalse(result.ok)
        self.assertFalse(os.path.exists(path))

    def test_rejects_invalid_image_when_requested(self):
        path = self._write_file("image.png", b"not-an-image")

        result = validate_media_file(path, expected_kind="image")

        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
