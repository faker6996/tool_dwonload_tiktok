import sys
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication, QStackedWidget, QToolButton, QButtonGroup
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta
from src.ui.pages.edit_page import EditPage
from src.ui.pages.download_page import DownloadPage
from src.ui.pages.document_page import DocumentPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Video Downloader & Editor")
        self.resize(1280, 720)
        self.setMinimumSize(1024, 600)
        
        self.setup_ui()
        
        # Setup queue manager early so badge updates work
        self._setup_queue_manager()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Layout (Vertical: Top Bar + Content)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Top Bar ---
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(50)
        self.top_bar.setStyleSheet("background-color: #18181b; border-bottom: 1px solid #27272a;")
        
        top_bar_layout = QHBoxLayout(self.top_bar)
        top_bar_layout.setContentsMargins(16, 0, 16, 0)
        
        # Title
        self.title_label = QLabel("Universal Video Downloader")
        self.title_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #e5e5e5;")
        top_bar_layout.addWidget(self.title_label)
        
        top_bar_layout.addStretch()
        
        # Queue Button with badge (shows popup panel)
        queue_container = QWidget()
        queue_container.setFixedSize(44, 44)
        queue_container_layout = QHBoxLayout(queue_container)
        queue_container_layout.setContentsMargins(0, 0, 0, 0)
        queue_container_layout.setSpacing(0)
        
        self.queue_btn = QPushButton("📋")
        self.queue_btn.setFixedSize(36, 36)
        self.queue_btn.setToolTip("Task Queue")
        self.queue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.queue_btn.setStyleSheet("""
            QPushButton {
                background: #27272a;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #3f3f46;
            }
        """)
        self.queue_btn.clicked.connect(self._toggle_queue_panel)
        queue_container_layout.addWidget(self.queue_btn)
        
        # Queue badge (positioned at top-right like iOS)
        self.queue_stats = QLabel("0")
        self.queue_stats.setParent(queue_container)
        self.queue_stats.setFixedSize(20, 20)
        self.queue_stats.setStyleSheet("""
            QLabel {
                background: #ef4444;
                color: white;
                font-size: 11px;
                font-weight: bold;
                border-radius: 10px;
                border: 2px solid #18181b;
            }
        """)
        self.queue_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.queue_stats.move(28, -2)  # Position at top-right corner
        self.queue_stats.raise_()  # Ensure it's on top
        self.queue_stats.hide()  # Hidden when 0 tasks
        
        top_bar_layout.addWidget(queue_container)
        
        # Spacer
        top_bar_layout.addSpacing(8)
        
        # Export Button
        self.export_btn = QPushButton("Export Video")
        self.export_btn.setObjectName("primary")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet("""
            QPushButton#primary {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #8a2be2, stop:1 #4b0082);
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 6px;
                border: none;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #6bb4ff, stop:1 #9d6fff);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #4a8fd9, stop:1 #7645d9);
            }
        """)
        self.export_btn.clicked.connect(self.on_export_clicked)
        self.export_btn.hide() # Hidden by default
        top_bar_layout.addWidget(self.export_btn)
        
        main_layout.addWidget(self.top_bar)

        # --- Content Area (Horizontal: Nav + Stack) ---
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 1. Left Navigation (Fixed Width)
        self.nav_bar = QFrame()
        self.nav_bar.setFixedWidth(80)
        self.nav_bar.setStyleSheet("background-color: #18181b; border-right: 1px solid #27272a;")
        
        nav_layout = QVBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(0, 10, 0, 10)
        nav_layout.setSpacing(10)
        
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_group.idClicked.connect(self.on_nav_clicked)
        
        # Add Nav Items (Edit first, Download second)
        self.add_nav_item(nav_layout, "edit", "Edit", 0)
        self.add_nav_item(nav_layout, "download", "Download", 1)
        self.add_nav_item(nav_layout, "file-alt", "Document", 2)
        self.add_nav_item(nav_layout, "cog", "Settings", 3)
        
        nav_layout.addStretch()
        content_layout.addWidget(self.nav_bar)
        
        # 2. Stacked Widget
        self.stacked_widget = QStackedWidget()
        
        self.edit_page = EditPage()
        self.download_page = DownloadPage()
        self.document_page = DocumentPage()
        
        # Index mapping must match nav IDs:
        # 0: Edit, 1: Download, 2: Document
        self.stacked_widget.addWidget(self.edit_page)      # index 0
        self.stacked_widget.addWidget(self.download_page)  # index 1
        self.stacked_widget.addWidget(self.document_page)  # index 2
        
        content_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(content_widget)
        
        # Set default page (Edit)
        self.nav_group.button(0).setChecked(True)
        self.on_nav_clicked(0)

    def add_nav_item(self, layout, icon_name, tooltip, id, checked=False):
        btn = QToolButton()
        btn.setFixedSize(60, 60)
        btn.setIcon(qta.icon(f"fa5s.{icon_name}", color="#a1a1aa"))
        btn.setIconSize(QSize(24, 24))
        btn.setToolTip(tooltip)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Style
        btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                border-radius: 8px;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
            QToolButton:checked {
                background-color: rgba(79, 70, 229, 0.1);
            }
        """)
        
        layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)
        self.nav_group.addButton(btn, id)

    def on_nav_clicked(self, id):
        if id == 3:
            # Settings
            self.open_settings()
            # Restore previous selection if needed, or just keep it checked?
            # For now, let's keep the previous page visible but the settings button checked?
            # Or maybe Settings should be a dialog and not change the page.
            # If it's a dialog, we should probably uncheck the button or not make it part of the exclusive group in the same way.
            # But for simplicity, let's just open the dialog and keep the current page.
            # We need to know the previous ID to restore check state if we want.
            # Let's just return for now, the button will stay checked which might be confusing if the page didn't change.
            # Better: Reset check to current page index.
            current_idx = self.stacked_widget.currentIndex()
            self.nav_group.button(current_idx).setChecked(True)
            return

        self.stacked_widget.setCurrentIndex(id)
        
        # Update UI based on page
        if id == 0: # Edit Page
            self.export_btn.show()
            self.title_label.setText("Video Editor")
        else:
            self.export_btn.hide()
            self.title_label.setText("Universal Video Downloader")

    def open_settings(self):
        """Open settings dialog."""
        from src.ui.dialogs.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()

    def on_export_clicked(self):
        if hasattr(self.edit_page, 'open_export_dialog'):
            self.edit_page.open_export_dialog()
    
    def _setup_queue_manager(self):
        """Setup queue manager and panel."""
        from src.core.queue_manager import queue_manager
        from src.ui.panels.queue_panel import QueuePanel
        
        self.queue_manager = queue_manager
        
        # Create queue panel (popup)
        self.queue_panel = QueuePanel(queue_manager)
        self.queue_panel.setParent(self)
        self.queue_panel.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.queue_panel.setFixedSize(360, 400)
        self.queue_panel.hide()
        
        # Connect to update badge
        queue_manager.task_added.connect(self._update_queue_badge)
        queue_manager.task_updated.connect(self._update_queue_badge)
        queue_manager.task_removed.connect(lambda _: self._update_queue_badge())
        queue_manager.queue_cleared.connect(self._update_queue_badge)
    
    def _toggle_queue_panel(self):
        """Show/hide the queue panel popup."""
        if not hasattr(self, 'queue_panel'):
            self._setup_queue_manager()
        
        if self.queue_panel.isVisible():
            self.queue_panel.hide()
        else:
            # Position below the queue button
            btn_pos = self.queue_btn.mapToGlobal(self.queue_btn.rect().bottomLeft())
            self.queue_panel.move(btn_pos.x() - 280, btn_pos.y() + 5)
            self.queue_panel.show()
    
    def _update_queue_badge(self, *args):
        """Update the queue badge with current task count."""
        if not hasattr(self, 'queue_manager'):
            return
        
        stats = self.queue_manager.get_stats()
        active = stats['pending'] + stats['running']
        
        if active > 0:
            self.queue_stats.setText(str(active))
            self.queue_stats.show()
        else:
            self.queue_stats.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
