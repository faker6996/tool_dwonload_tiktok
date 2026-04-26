from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict, Optional
import uuid


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
class QueueTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_type: TaskType = TaskType.DOWNLOAD
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    title: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.task_type.value,
            "status": self.status.value,
            "progress": self.progress,
            "title": self.title,
            "error": self.error,
        }


def clamp_progress(progress: int) -> int:
    try:
        value = int(progress)
    except Exception:
        value = 0
    return max(0, min(100, value))


def can_transition(current: TaskStatus, target: TaskStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def transition_task(
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
    return transition_task(task, TaskStatus.CANCELLED)


def clear_terminal_tasks(tasks: list[QueueTask]) -> list[QueueTask]:
    return [task for task in tasks if task.status not in TERMINAL_STATUSES]


def task_status_counts(tasks: list[QueueTask]) -> dict[str, int]:
    return {
        "total": len(tasks),
        "pending": sum(1 for task in tasks if task.status == TaskStatus.PENDING),
        "running": sum(1 for task in tasks if task.status == TaskStatus.RUNNING),
        "completed": sum(1 for task in tasks if task.status == TaskStatus.COMPLETED),
        "failed": sum(1 for task in tasks if task.status == TaskStatus.FAILED),
        "cancelled": sum(1 for task in tasks if task.status == TaskStatus.CANCELLED),
    }
