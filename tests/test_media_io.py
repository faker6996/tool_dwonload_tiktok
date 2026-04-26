import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.media_io import (
    atomic_replace_validated,
    copy_file_atomic,
    make_temp_path,
    stable_file_cache_key,
    stable_file_hash,
)


class TestMediaIO(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_file(self, name: str, content: bytes) -> str:
        path = os.path.join(self.temp_dir, name)
        with open(path, "wb") as file_obj:
            file_obj.write(content)
        return path

    def test_make_temp_path_uses_destination_directory(self):
        destination = os.path.join(self.temp_dir, "nested", "video.mp4")

        temp_path = make_temp_path(destination)

        self.assertTrue(temp_path.startswith(os.path.dirname(destination)))
        self.assertTrue(os.path.exists(temp_path))
        os.remove(temp_path)

    def test_atomic_replace_validated_replaces_valid_file(self):
        temp_path = self._write_file("temp.part", b"video-bytes")
        destination = os.path.join(self.temp_dir, "video.mp4")

        result = atomic_replace_validated(temp_path, destination)

        self.assertTrue(result.ok)
        self.assertEqual(result.path, destination)
        self.assertFalse(os.path.exists(temp_path))
        with open(destination, "rb") as file_obj:
            self.assertEqual(file_obj.read(), b"video-bytes")

    def test_atomic_replace_validated_removes_invalid_file(self):
        temp_path = self._write_file("temp.part", b"<html>forbidden</html>")
        destination = os.path.join(self.temp_dir, "video.mp4")

        result = atomic_replace_validated(temp_path, destination)

        self.assertFalse(result.ok)
        self.assertFalse(os.path.exists(temp_path))
        self.assertFalse(os.path.exists(destination))

    def test_copy_file_atomic_reports_progress_and_validates(self):
        source = self._write_file("source.mp4", b"video-bytes")
        destination = os.path.join(self.temp_dir, "out.mp4")
        events = []

        result = copy_file_atomic(
            source,
            destination,
            progress_callback=lambda done, total: events.append((done, total)),
            chunk_size=5,
        )

        self.assertTrue(result.ok)
        self.assertTrue(os.path.exists(destination))
        self.assertTrue(events)
        self.assertEqual(events[-1], (len(b"video-bytes"), len(b"video-bytes")))

    def test_copy_file_atomic_rejects_invalid_source(self):
        source = self._write_file("source.mp4", b"<html>not found</html>")
        destination = os.path.join(self.temp_dir, "out.mp4")

        result = copy_file_atomic(source, destination)

        self.assertFalse(result.ok)
        self.assertFalse(os.path.exists(destination))

    def test_stable_file_hash_changes_with_file_state(self):
        path = self._write_file("source.mp4", b"one")
        first_key = stable_file_cache_key(path)
        first_hash = stable_file_hash(path)

        with open(path, "ab") as file_obj:
            file_obj.write(b"two")

        self.assertNotEqual(first_key, stable_file_cache_key(path))
        self.assertNotEqual(first_hash, stable_file_hash(path))


if __name__ == "__main__":
    unittest.main()
