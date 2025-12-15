"""
Queue Manager - Background Task Processing System
Handles download, translate, remove sub, and export tasks without blocking UI.
"""
import uuid
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable, Any
from enum import Enum
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QMutex, QWaitCondition


class TaskType(Enum):
    DOWNLOAD = "download"
    TRANSLATE = "translate"
    REMOVE_SUB = "remove_sub"
    EXPORT = "export"
    TRANSCODE = "transcode"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueTask:
    """Represents a single task in the queue."""
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
            "error": self.error
        }


class QueueWorker(QThread):
    """Worker thread that processes tasks from the queue."""
    task_started = pyqtSignal(str)  # task_id
    task_progress = pyqtSignal(str, int)  # task_id, progress
    task_completed = pyqtSignal(str)  # task_id
    task_failed = pyqtSignal(str, str)  # task_id, error
    
    def __init__(self, queue_manager: 'QueueManager'):
        super().__init__()
        self.queue_manager = queue_manager
        self._running = True
        self._paused = False
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        
        # Task handlers registered by type
        self._handlers: Dict[TaskType, Callable] = {}
    
    def register_handler(self, task_type: TaskType, handler: Callable):
        """Register a handler function for a task type."""
        self._handlers[task_type] = handler
    
    def pause(self):
        self._paused = True
    
    def resume(self):
        self._paused = False
        self._condition.wakeAll()
    
    def stop(self):
        self._running = False
        self._condition.wakeAll()
    
    def run(self):
        while self._running:
            # Check if paused
            self._mutex.lock()
            while self._paused and self._running:
                self._condition.wait(self._mutex)
            self._mutex.unlock()
            
            if not self._running:
                break
            
            # Get next pending task
            task = self.queue_manager.get_next_pending_task()
            if task is None:
                # No tasks, sleep and check again
                time.sleep(0.5)
                continue
            
            # Process the task
            self._process_task(task)
    
    def _process_task(self, task: QueueTask):
        """Process a single task."""
        task.status = TaskStatus.RUNNING
        self.task_started.emit(task.id)
        
        handler = self._handlers.get(task.task_type)
        if handler is None:
            task.status = TaskStatus.FAILED
            task.error = f"No handler for task type: {task.task_type.value}"
            self.task_failed.emit(task.id, task.error)
            return
        
        try:
            # Define progress callback
            def progress_callback(progress: int):
                task.progress = progress
                self.task_progress.emit(task.id, progress)
            
            # Run the handler
            handler(task.data, progress_callback)
            
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            self.task_completed.emit(task.id)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.task_failed.emit(task.id, str(e))


class QueueManager(QObject):
    """Manages the task queue and worker threads."""
    
    # Signals for UI updates
    task_added = pyqtSignal(object)  # QueueTask
    task_updated = pyqtSignal(object)  # QueueTask
    task_removed = pyqtSignal(str)  # task_id
    queue_cleared = pyqtSignal()
    
    def __init__(self, max_workers: int = 1):
        super().__init__()
        self._tasks: List[QueueTask] = []
        self._mutex = QMutex()
        self._max_workers = max_workers
        self._workers: List[QueueWorker] = []
        self._is_paused = False
        
        # Start workers
        self._start_workers()
    
    def _start_workers(self):
        """Start worker threads."""
        for i in range(self._max_workers):
            worker = QueueWorker(self)
            worker.task_started.connect(self._on_task_started)
            worker.task_progress.connect(self._on_task_progress)
            worker.task_completed.connect(self._on_task_completed)
            worker.task_failed.connect(self._on_task_failed)
            self._workers.append(worker)
            worker.start()
    
    def register_handler(self, task_type: TaskType, handler: Callable):
        """Register a handler for all workers."""
        for worker in self._workers:
            worker.register_handler(task_type, handler)
    
    def add_task(self, task_type: TaskType, title: str, data: dict) -> QueueTask:
        """Add a new task to the queue."""
        task = QueueTask(
            task_type=task_type,
            title=title,
            data=data
        )
        
        self._mutex.lock()
        self._tasks.append(task)
        self._mutex.unlock()
        
        self.task_added.emit(task)
        print(f"📋 Task added: [{task.task_type.value}] {task.title}")
        return task
    
    def get_next_pending_task(self) -> Optional[QueueTask]:
        """Get the next pending task from the queue."""
        self._mutex.lock()
        for task in self._tasks:
            if task.status == TaskStatus.PENDING:
                self._mutex.unlock()
                return task
        self._mutex.unlock()
        return None
    
    def get_task(self, task_id: str) -> Optional[QueueTask]:
        """Get a task by ID."""
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[QueueTask]:
        """Get all tasks."""
        return self._tasks.copy()
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            self.task_updated.emit(task)
            return True
        return False
    
    def remove_task(self, task_id: str):
        """Remove a task from the queue."""
        self._mutex.lock()
        self._tasks = [t for t in self._tasks if t.id != task_id]
        self._mutex.unlock()
        self.task_removed.emit(task_id)
    
    def clear_completed(self):
        """Clear all completed/failed/cancelled tasks."""
        self._mutex.lock()
        self._tasks = [t for t in self._tasks if t.status in 
                       [TaskStatus.PENDING, TaskStatus.RUNNING]]
        self._mutex.unlock()
        self.queue_cleared.emit()
    
    def pause_queue(self):
        """Pause all workers."""
        self._is_paused = True
        for worker in self._workers:
            worker.pause()
    
    def resume_queue(self):
        """Resume all workers."""
        self._is_paused = False
        for worker in self._workers:
            worker.resume()
    
    def is_paused(self) -> bool:
        return self._is_paused
    
    def get_stats(self) -> dict:
        """Get queue statistics."""
        pending = sum(1 for t in self._tasks if t.status == TaskStatus.PENDING)
        running = sum(1 for t in self._tasks if t.status == TaskStatus.RUNNING)
        completed = sum(1 for t in self._tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self._tasks if t.status == TaskStatus.FAILED)
        
        return {
            "total": len(self._tasks),
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed
        }
    
    def _on_task_started(self, task_id: str):
        task = self.get_task(task_id)
        if task:
            self.task_updated.emit(task)
    
    def _on_task_progress(self, task_id: str, progress: int):
        task = self.get_task(task_id)
        if task:
            self.task_updated.emit(task)
    
    def _on_task_completed(self, task_id: str):
        task = self.get_task(task_id)
        if task:
            self.task_updated.emit(task)
    
    def _on_task_failed(self, task_id: str, error: str):
        task = self.get_task(task_id)
        if task:
            self.task_updated.emit(task)
    
    def shutdown(self):
        """Shutdown all workers gracefully."""
        for worker in self._workers:
            worker.stop()
        for worker in self._workers:
            worker.wait()


# Global queue manager instance
queue_manager = QueueManager(max_workers=1)
