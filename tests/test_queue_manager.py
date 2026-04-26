import os
import sys
import unittest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.queue_manager import QueueManager, TaskType, TaskStatus


class TestQueueManager(unittest.TestCase):
    def setUp(self):
        self.queue = QueueManager(max_workers=0)

    def tearDown(self):
        self.queue.shutdown()

    def test_lazy_start_on_add_task(self):
        self.assertFalse(self.queue._workers_started)
        self.queue.add_task(TaskType.DOWNLOAD, "download", {"x": 1})
        self.assertTrue(self.queue._workers_started)

    def test_task_added_before_handler_is_not_failed(self):
        task = self.queue.add_task(TaskType.DOWNLOAD, "download", {"ran": False})

        self.assertNotEqual(task.status, TaskStatus.FAILED)
        self.assertEqual(task.status, TaskStatus.PENDING)

        def handle_download(data, progress_callback):
            progress_callback(50)
            data["ran"] = True

        self.queue.register_handler(TaskType.DOWNLOAD, handle_download)

        self.assertIs(self.queue.get_handler(TaskType.DOWNLOAD), handle_download)
        self.assertEqual(task.status, TaskStatus.PENDING)

    def test_claiming_next_task_marks_running_before_returning(self):
        queue = QueueManager(max_workers=0)
        try:
            first = queue.add_task(TaskType.DOWNLOAD, "download 1", {"id": 1})
            second = queue.add_task(TaskType.DOWNLOAD, "download 2", {"id": 2})

            claimed_first = queue.get_next_pending_task()
            claimed_second = queue.get_next_pending_task()
            claimed_third = queue.get_next_pending_task()

            self.assertEqual(claimed_first.id, first.id)
            self.assertEqual(claimed_second.id, second.id)
            self.assertIsNone(claimed_third)
            self.assertEqual(first.status, TaskStatus.RUNNING)
            self.assertEqual(second.status, TaskStatus.RUNNING)
        finally:
            queue.shutdown()

    def test_cancel_and_clear_completed_use_core_rules(self):
        pending = self.queue.add_task(TaskType.DOWNLOAD, "pending", {})
        self.assertTrue(self.queue.cancel_task(pending.id))
        self.assertFalse(self.queue.cancel_task(pending.id))

        stats = self.queue.get_stats()
        self.assertEqual(stats["cancelled"], 1)

        self.queue.clear_completed()
        self.assertIsNone(self.queue.get_task(pending.id))


if __name__ == "__main__":
    unittest.main()
