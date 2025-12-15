"""
Queue Panel - UI for displaying and managing background tasks.
Shows as a popup/panel with task list, progress, and controls.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

from src.core.queue_manager import QueueManager, QueueTask, TaskStatus, TaskType


class QueueTaskWidget(QFrame):
    """Widget representing a single task in the queue."""
    
    STATUS_ICONS = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.RUNNING: "▶️",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.FAILED: "❌",
        TaskStatus.CANCELLED: "🚫"
    }
    
    TYPE_COLORS = {
        TaskType.DOWNLOAD: "#3b82f6",     # Blue
        TaskType.TRANSLATE: "#8b5cf6",    # Purple
        TaskType.REMOVE_SUB: "#f59e0b",   # Orange
        TaskType.EXPORT: "#10b981",       # Green
        TaskType.TRANSCODE: "#6366f1"     # Indigo
    }
    
    def __init__(self, task: QueueTask, queue_manager: QueueManager):
        super().__init__()
        self.task = task
        self.queue_manager = queue_manager
        self._setup_ui()
        self.update_display()
    
    def _setup_ui(self):
        self.setObjectName("queueTaskWidget")
        self.setStyleSheet("""
            #queueTaskWidget {
                background: #1f1f23;
                border-radius: 8px;
                padding: 8px;
                margin: 4px 0;
            }
            #queueTaskWidget:hover {
                background: #2a2a30;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # Top row: Icon + Title + Action buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        # Status icon
        self.status_icon = QLabel("⏳")
        self.status_icon.setFont(QFont("", 14))
        top_row.addWidget(self.status_icon)
        
        # Task type badge
        self.type_badge = QLabel()
        self.type_badge.setFont(QFont("", 9))
        top_row.addWidget(self.type_badge)
        
        # Title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("color: #e4e4e7; font-size: 12px;")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_row.addWidget(self.title_label)
        
        # Cancel button
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setFixedSize(24, 24)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #71717a;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #ef4444;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        top_row.addWidget(self.cancel_btn)
        
        layout.addLayout(top_row)
        
        # Progress bar (only shown when running)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #27272a;
                border-radius: 6px;
                text-align: center;
                font-size: 9px;
                color: #a1a1aa;
            }
            QProgressBar::chunk {
                background: #3b82f6;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Error message (only shown when failed)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #ef4444; font-size: 10px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
    
    def update_display(self):
        """Update the widget display based on task state."""
        self.status_icon.setText(self.STATUS_ICONS.get(self.task.status, "❓"))
        self.title_label.setText(self.task.title)
        
        # Type badge
        type_color = self.TYPE_COLORS.get(self.task.task_type, "#6b7280")
        self.type_badge.setText(self.task.task_type.value.upper())
        self.type_badge.setStyleSheet(f"""
            background: {type_color}33;
            color: {type_color};
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: bold;
        """)
        
        # Progress bar visibility
        if self.task.status == TaskStatus.RUNNING:
            self.progress_bar.show()
            self.progress_bar.setValue(self.task.progress)
        else:
            self.progress_bar.hide()
        
        # Cancel button visibility
        if self.task.status in [TaskStatus.PENDING]:
            self.cancel_btn.show()
        else:
            self.cancel_btn.hide()
        
        # Error message
        if self.task.status == TaskStatus.FAILED and self.task.error:
            self.error_label.setText(f"Error: {self.task.error}")
            self.error_label.show()
        else:
            self.error_label.hide()
    
    def _on_cancel(self):
        self.queue_manager.cancel_task(self.task.id)


class QueuePanel(QWidget):
    """Panel showing all queue tasks with controls."""
    
    def __init__(self, queue_manager: QueueManager):
        super().__init__()
        self.queue_manager = queue_manager
        self.task_widgets: dict[str, QueueTaskWidget] = {}
        
        self._setup_ui()
        self._connect_signals()
        
        # Load existing tasks
        for task in self.queue_manager.get_all_tasks():
            self._add_task_widget(task)
    
    def _setup_ui(self):
        self.setObjectName("queuePanel")
        self.setMinimumWidth(320)
        self.setStyleSheet("""
            #queuePanel {
                background: #18181b;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📋 Queue")
        title.setStyleSheet("color: #fafafa; font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        
        self.stats_label = QLabel("0 tasks")
        self.stats_label.setStyleSheet("color: #71717a; font-size: 12px;")
        header.addWidget(self.stats_label)
        
        header.addStretch()
        
        # Pause/Resume button
        self.pause_btn = QPushButton("⏸️")
        self.pause_btn.setFixedSize(32, 32)
        self.pause_btn.setToolTip("Pause Queue")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: #27272a;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #3f3f46;
            }
        """)
        self.pause_btn.clicked.connect(self._toggle_pause)
        header.addWidget(self.pause_btn)
        
        # Clear completed button
        clear_btn = QPushButton("🗑️")
        clear_btn.setFixedSize(32, 32)
        clear_btn.setToolTip("Clear Completed")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #27272a;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #3f3f46;
            }
        """)
        clear_btn.clicked.connect(self._on_clear_completed)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        # Separator
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: #27272a;")
        layout.addWidget(separator)
        
        # Scroll area for tasks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
            }
            QScrollBar:vertical {
                background: #27272a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #3f3f46;
                border-radius: 4px;
            }
        """)
        
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(0, 0, 0, 0)
        self.task_layout.setSpacing(4)
        self.task_layout.addStretch()
        
        scroll.setWidget(self.task_container)
        layout.addWidget(scroll)
        
        # Empty state
        self.empty_label = QLabel("No tasks in queue")
        self.empty_label.setStyleSheet("color: #52525b; font-size: 12px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)
        
        self._update_empty_state()
    
    def _connect_signals(self):
        self.queue_manager.task_added.connect(self._on_task_added)
        self.queue_manager.task_updated.connect(self._on_task_updated)
        self.queue_manager.task_removed.connect(self._on_task_removed)
        self.queue_manager.queue_cleared.connect(self._on_queue_cleared)
    
    @pyqtSlot(object)
    def _on_task_added(self, task: QueueTask):
        self._add_task_widget(task)
    
    @pyqtSlot(object)
    def _on_task_updated(self, task: QueueTask):
        widget = self.task_widgets.get(task.id)
        if widget:
            widget.update_display()
        self._update_stats()
    
    @pyqtSlot(str)
    def _on_task_removed(self, task_id: str):
        widget = self.task_widgets.pop(task_id, None)
        if widget:
            widget.deleteLater()
        self._update_empty_state()
        self._update_stats()
    
    @pyqtSlot()
    def _on_queue_cleared(self):
        # Remove completed task widgets
        for task_id, widget in list(self.task_widgets.items()):
            task = self.queue_manager.get_task(task_id)
            if task is None:
                widget.deleteLater()
                del self.task_widgets[task_id]
        self._update_empty_state()
        self._update_stats()
    
    def _add_task_widget(self, task: QueueTask):
        widget = QueueTaskWidget(task, self.queue_manager)
        self.task_widgets[task.id] = widget
        # Insert before the stretch
        self.task_layout.insertWidget(self.task_layout.count() - 1, widget)
        self._update_empty_state()
        self._update_stats()
    
    def _update_empty_state(self):
        has_tasks = len(self.task_widgets) > 0
        self.empty_label.setVisible(not has_tasks)
    
    def _update_stats(self):
        stats = self.queue_manager.get_stats()
        self.stats_label.setText(f"{stats['running']}/{stats['total']} running")
    
    def _toggle_pause(self):
        if self.queue_manager.is_paused():
            self.queue_manager.resume_queue()
            self.pause_btn.setText("⏸️")
            self.pause_btn.setToolTip("Pause Queue")
        else:
            self.queue_manager.pause_queue()
            self.pause_btn.setText("▶️")
            self.pause_btn.setToolTip("Resume Queue")
    
    def _on_clear_completed(self):
        self.queue_manager.clear_completed()
