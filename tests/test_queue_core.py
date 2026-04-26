import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.queue_core import (
    QueueTask,
    TaskStatus,
    TaskType,
    cancel_pending_task,
    claim_next_pending_task,
    clear_terminal_tasks,
    clamp_progress,
    task_status_counts,
    transition_task,
    update_task_progress,
)


class TestQueueCore(unittest.TestCase):
    def test_claim_next_pending_task_marks_running_once(self):
        tasks = [
            QueueTask(id="a", task_type=TaskType.DOWNLOAD),
            QueueTask(id="b", task_type=TaskType.EXPORT),
        ]

        first = claim_next_pending_task(tasks)
        second = claim_next_pending_task(tasks)
        third = claim_next_pending_task(tasks)

        self.assertEqual(first.id, "a")
        self.assertEqual(second.id, "b")
        self.assertIsNone(third)
        self.assertEqual(tasks[0].status, TaskStatus.RUNNING)
        self.assertEqual(tasks[1].status, TaskStatus.RUNNING)

    def test_terminal_tasks_cannot_transition_again(self):
        task = QueueTask(status=TaskStatus.COMPLETED)

        changed = transition_task(task, TaskStatus.RUNNING)

        self.assertFalse(changed)
        self.assertEqual(task.status, TaskStatus.COMPLETED)

    def test_cancel_only_pending_task(self):
        pending = QueueTask(status=TaskStatus.PENDING)
        running = QueueTask(status=TaskStatus.RUNNING)

        self.assertTrue(cancel_pending_task(pending))
        self.assertFalse(cancel_pending_task(running))
        self.assertEqual(pending.status, TaskStatus.CANCELLED)
        self.assertEqual(running.status, TaskStatus.RUNNING)

    def test_progress_updates_only_running_and_clamps(self):
        running = QueueTask(status=TaskStatus.RUNNING)
        pending = QueueTask(status=TaskStatus.PENDING)

        self.assertTrue(update_task_progress(running, 150))
        self.assertFalse(update_task_progress(pending, 50))
        self.assertEqual(running.progress, 100)
        self.assertEqual(pending.progress, 0)
        self.assertEqual(clamp_progress(-20), 0)

    def test_clear_terminal_tasks_preserves_active(self):
        tasks = [
            QueueTask(status=TaskStatus.PENDING),
            QueueTask(status=TaskStatus.RUNNING),
            QueueTask(status=TaskStatus.COMPLETED),
            QueueTask(status=TaskStatus.FAILED),
            QueueTask(status=TaskStatus.CANCELLED),
        ]

        active = clear_terminal_tasks(tasks)

        self.assertEqual([task.status for task in active], [TaskStatus.PENDING, TaskStatus.RUNNING])

    def test_task_status_counts_include_cancelled(self):
        tasks = [
            QueueTask(status=TaskStatus.PENDING),
            QueueTask(status=TaskStatus.RUNNING),
            QueueTask(status=TaskStatus.CANCELLED),
        ]

        self.assertEqual(
            task_status_counts(tasks),
            {
                "total": 3,
                "pending": 1,
                "running": 1,
                "completed": 0,
                "failed": 0,
                "cancelled": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
