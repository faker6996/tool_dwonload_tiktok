import os
import sys
import time
import unittest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.queue_manager import QueueManager, TaskType, TaskStatus


class TestQueueManager(unittest.TestCase):
    def setUp(self):
        self.queue = QueueManager(max_workers=1)

    def tearDown(self):
        self.queue.shutdown()

    def test_lazy_start_on_add_task(self):
        self.assertFalse(self.queue._workers_started)
        self.queue.add_task(TaskType.DOWNLOAD, "download", {"x": 1})
        self.assertTrue(self.queue._workers_started)

    def test_task_added_before_handler_is_not_failed(self):
        task = self.queue.add_task(TaskType.DOWNLOAD, "download", {"ran": False})

        # Let worker attempt before handler is registered
        time.sleep(0.2)
        self.assertNotEqual(task.status, TaskStatus.FAILED)

        def handle_download(data, progress_callback):
            progress_callback(50)
            data["ran"] = True

        self.queue.register_handler(TaskType.DOWNLOAD, handle_download)

        deadline = time.time() + 3.0
        while time.time() < deadline and task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            time.sleep(0.05)

        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertTrue(task.data["ran"])


if __name__ == "__main__":
    unittest.main()
