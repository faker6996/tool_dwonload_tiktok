import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.core.queue_core as queue_core
from src.core.queue_core import (
    QueueTask,
    TaskStatus,
    TaskType,
    cancel_pending_task,
    claim_next_pending_task,
    clear_terminal_tasks,
    clamp_progress,
    request_task_cancellation,
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

    def test_running_cancellation_sets_token_and_status(self):
        task = QueueTask(status=TaskStatus.RUNNING)

        changed = request_task_cancellation(task, "user cancelled")

        self.assertTrue(changed)
        self.assertEqual(task.status, TaskStatus.CANCELLED)
        self.assertTrue(task.cancellation_token.is_cancelled())
        self.assertEqual(task.cancellation_token.reason, "user cancelled")
        self.assertEqual(task.error, "user cancelled")

    def test_cancel_requested_is_serialized(self):
        task = QueueTask(status=TaskStatus.PENDING)
        request_task_cancellation(task)

        self.assertTrue(task.to_dict()["cancelRequested"])

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

    def test_native_queue_core_result_is_applied_when_available(self):
        original_native = queue_core._video_core

        class FakeNativeQueueCore:
            def queue_transition_json(
                self,
                current_status,
                current_progress,
                current_error,
                target_status,
                progress=None,
                error=None,
            ):
                self.last_transition = (
                    current_status,
                    current_progress,
                    current_error,
                    target_status,
                    progress,
                    error,
                )
                return (
                    '{"ok": true, "status": "running", '
                    '"progress": 42, "error": null}'
                )

            def queue_request_cancellation_json(
                self,
                current_status,
                current_progress,
                current_error,
                reason="cancelled",
            ):
                return (
                    '{"ok": true, "status": "cancelled", "progress": 42, '
                    '"error": "stop", "cancel_requested": true, "cancel_reason": "stop"}'
                )

            def queue_status_counts_json(self, statuses_json):
                return (
                    '{"total": 2, "pending": 1, "running": 1, '
                    '"completed": 0, "failed": 0, "cancelled": 0}'
                )

            def queue_clamp_progress(self, progress):
                return 42

            def queue_can_transition(self, current_status, target_status):
                return True

        try:
            fake_native = FakeNativeQueueCore()
            queue_core._video_core = fake_native
            task = QueueTask(status=TaskStatus.PENDING)

            self.assertTrue(transition_task(task, TaskStatus.RUNNING, progress=7))
            self.assertEqual(task.status, TaskStatus.RUNNING)
            self.assertEqual(task.progress, 42)
            self.assertTrue(request_task_cancellation(task, "stop"))
            self.assertTrue(task.cancellation_token.is_cancelled())
            self.assertEqual(task.error, "stop")
            self.assertEqual(task_status_counts([QueueTask(), QueueTask(status=TaskStatus.RUNNING)])["running"], 1)
        finally:
            queue_core._video_core = original_native


if __name__ == "__main__":
    unittest.main()
