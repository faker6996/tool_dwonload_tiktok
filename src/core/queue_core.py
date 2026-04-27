from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import time
from typing import Any, Dict, Optional
import uuid

try:
    import video_core as _video_core
except ImportError:
    _video_core = None


class TaskType(Enum):
    DOWNLOAD = "download"
    TRANSLATE = "translate"
    REMOVE_SUB = "remove_sub"
    EXPORT = "export"
    TRANSCODE = "transcode"
    OCR_EXTRACT = "ocr_extract"
    TRANSCRIBE = "transcribe"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATUSES = {
    TaskStatus.COMPLETED,
    TaskStatus.FAILED,
    TaskStatus.CANCELLED,
}


ALLOWED_TRANSITIONS = {
    TaskStatus.PENDING: {
        TaskStatus.RUNNING,
        TaskStatus.CANCELLED,
    },
    TaskStatus.RUNNING: {
        TaskStatus.PENDING,
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
}


@dataclass
class CancellationToken:
    requested: bool = False
    reason: str = ""

    def cancel(self, reason: str = "cancelled") -> None:
        self.requested = True
        self.reason = reason

    def is_cancelled(self) -> bool:
        return self.requested


@dataclass
class QueueTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_type: TaskType = TaskType.DOWNLOAD
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    title: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.task_type.value,
            "status": self.status.value,
            "progress": self.progress,
            "title": self.title,
            "error": self.error,
            "cancelRequested": self.cancellation_token.is_cancelled(),
        }


def clamp_progress(progress: int) -> int:
    if _has_native_queue_core():
        try:
            return int(_video_core.queue_clamp_progress(int(progress)))
        except Exception:
            pass
    try:
        value = int(progress)
    except Exception:
        value = 0
    return max(0, min(100, value))


def can_transition(current: TaskStatus, target: TaskStatus) -> bool:
    if _has_native_queue_core():
        try:
            return bool(_video_core.queue_can_transition(current.value, target.value))
        except Exception:
            pass
    return target in ALLOWED_TRANSITIONS.get(current, set())


def transition_task(
    task: QueueTask,
    target: TaskStatus,
    *,
    progress: Optional[int] = None,
    error: Optional[str] = None,
) -> bool:
    if _has_native_queue_core():
        result = _native_transition_task(task, target, progress=progress, error=error)
        if result is not None:
            return result

    return _transition_task_python(task, target, progress=progress, error=error)


def _transition_task_python(
    task: QueueTask,
    target: TaskStatus,
    *,
    progress: Optional[int] = None,
    error: Optional[str] = None,
) -> bool:
    if task.status == target:
        if progress is not None:
            task.progress = clamp_progress(progress)
        if error is not None:
            task.error = error
        return True

    if not can_transition(task.status, target):
        return False

    task.status = target
    if target == TaskStatus.PENDING:
        task.progress = 0
        task.error = None
    elif target == TaskStatus.RUNNING:
        task.error = None
        if progress is not None:
            task.progress = clamp_progress(progress)
    elif target == TaskStatus.COMPLETED:
        task.progress = 100
        task.error = None
    elif target == TaskStatus.FAILED:
        task.error = error or task.error
    elif target == TaskStatus.CANCELLED:
        task.error = error or task.error

    return True


def update_task_progress(task: QueueTask, progress: int) -> bool:
    if task.status != TaskStatus.RUNNING:
        return False
    task.progress = clamp_progress(progress)
    return True


def claim_next_pending_task(tasks: list[QueueTask]) -> Optional[QueueTask]:
    for task in tasks:
        if task.status == TaskStatus.PENDING:
            transition_task(task, TaskStatus.RUNNING, progress=task.progress)
            return task
    return None


def cancel_pending_task(task: QueueTask) -> bool:
    if task.status != TaskStatus.PENDING:
        return False
    task.cancellation_token.cancel()
    return transition_task(task, TaskStatus.CANCELLED)


def request_task_cancellation(
    task: QueueTask,
    reason: str = "cancelled",
) -> bool:
    if _has_native_queue_core():
        result = _native_request_task_cancellation(task, reason)
        if result is not None:
            return result

    if task.status == TaskStatus.PENDING:
        task.cancellation_token.cancel(reason)
        return transition_task(task, TaskStatus.CANCELLED, error=reason)
    if task.status == TaskStatus.RUNNING:
        task.cancellation_token.cancel(reason)
        return transition_task(task, TaskStatus.CANCELLED, error=reason)
    return False


def clear_terminal_tasks(tasks: list[QueueTask]) -> list[QueueTask]:
    return [task for task in tasks if task.status not in TERMINAL_STATUSES]


def task_status_counts(tasks: list[QueueTask]) -> dict[str, int]:
    if _has_native_queue_core():
        try:
            return json.loads(
                _video_core.queue_status_counts_json(
                    json.dumps([task.status.value for task in tasks])
                )
            )
        except Exception:
            pass
    return {
        "total": len(tasks),
        "pending": sum(1 for task in tasks if task.status == TaskStatus.PENDING),
        "running": sum(1 for task in tasks if task.status == TaskStatus.RUNNING),
        "completed": sum(1 for task in tasks if task.status == TaskStatus.COMPLETED),
        "failed": sum(1 for task in tasks if task.status == TaskStatus.FAILED),
        "cancelled": sum(1 for task in tasks if task.status == TaskStatus.CANCELLED),
    }


def _has_native_queue_core() -> bool:
    return (
        _video_core is not None
        and hasattr(_video_core, "queue_transition_json")
        and hasattr(_video_core, "queue_request_cancellation_json")
        and hasattr(_video_core, "queue_status_counts_json")
    )


def _native_transition_task(
    task: QueueTask,
    target: TaskStatus,
    *,
    progress: Optional[int] = None,
    error: Optional[str] = None,
) -> Optional[bool]:
    try:
        result = json.loads(
            _video_core.queue_transition_json(
                task.status.value,
                int(task.progress),
                task.error,
                target.value,
                progress,
                error,
            )
        )
    except Exception:
        return None

    if not result.get("ok"):
        return False

    _apply_native_task_state(task, result)
    return True


def _native_request_task_cancellation(task: QueueTask, reason: str) -> Optional[bool]:
    try:
        result = json.loads(
            _video_core.queue_request_cancellation_json(
                task.status.value,
                int(task.progress),
                task.error,
                reason,
            )
        )
    except Exception:
        return None

    if not result.get("ok"):
        return False

    task.cancellation_token.cancel(result.get("cancel_reason") or reason or "cancelled")
    _apply_native_task_state(task, result)
    return True


def _apply_native_task_state(task: QueueTask, result: dict) -> None:
    task.status = TaskStatus(result["status"])
    task.progress = clamp_progress(result.get("progress", task.progress))
    task.error = result.get("error")
