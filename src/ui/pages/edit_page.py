from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt

from ..panels.media_pool import MediaPool
from ..panels.player import Player
from ..panels.inspector import Inspector
from ..panels.timeline import Timeline

class EditPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header Area
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel
        header_widget = QWidget()
        header_widget.setFixedHeight(50)
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 rgba(30, 30, 30, 0.98), 
                                            stop:1 rgba(22, 27, 34, 0.95));
                border-bottom: 1px solid rgba(88, 166, 255, 0.2);
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        header_layout.addStretch()
        
        export_btn = QPushButton("🎬 Export Video")
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #58a6ff, stop:1 #8b5cf6);
                color: white;
                font-weight: bold;
                padding: 10px 24px;
                border-radius: 6px;
                border: none;
                font-size: 14px;
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
        export_btn.clicked.connect(self.open_export_dialog)
        header_layout.addWidget(export_btn)
        
        layout.addWidget(header_widget)

        # Main Vertical Splitter (Top: Workspace, Bottom: Timeline)
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.setHandleWidth(2)

        # Top Horizontal Splitter (Left Panel | Player | Inspector)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.setHandleWidth(2)

        # Left Panel (Tabs: Media Pool, Effects)
        from PyQt6.QtWidgets import QTabWidget
        from ..panels.effects import Effects
        
        self.left_panel = QTabWidget()
        self.left_panel.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: #1E1E1E; color: #BBB; padding: 5px 10px; }
            QTabBar::tab:selected { background: #2C2C2C; color: #FFF; }
        """)
        
        self.media_pool = MediaPool()
        self.effects = Effects()
        
        self.left_panel.addTab(self.media_pool, "Media")
        self.left_panel.addTab(self.effects, "Effects")

        self.player = Player()
        self.inspector = Inspector()
        self.timeline = Timeline()

        # Add to Top Splitter
        top_splitter.addWidget(self.left_panel)
        top_splitter.addWidget(self.player)
        top_splitter.addWidget(self.inspector)

        # Set initial sizes for top splitter (20% | 60% | 20%)
        # Note: We can't set exact pixels easily without window size, 
        # but we can set stretch factors or initial sizes if we knew the width.
        # For now, let's rely on default or setStretchFactor.
        top_splitter.setStretchFactor(0, 1) # Media Pool
        top_splitter.setStretchFactor(1, 3) # Player
        top_splitter.setStretchFactor(2, 2) # Inspector (Increased width)

        # Add to Main Splitter
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.timeline)

        # Set initial sizes for main splitter (60% Top | 40% Bottom)
        main_splitter.setStretchFactor(0, 6)
        main_splitter.setStretchFactor(1, 4)

        layout.addWidget(main_splitter)
        
        # Connect Signals
        # Note: self.timeline is the container panel, we need to access the widget inside
        if hasattr(self.timeline, 'timeline_widget'):
            self.timeline.timeline_widget.clip_selected.connect(self.inspector.set_clip)
            self.timeline.timeline_widget.clip_selected.connect(self.player.set_clip)
            
        self.inspector.clip_changed.connect(self.player.update_overlay)
        self.player.transform_changed.connect(lambda: self.inspector.set_clip(self.timeline.timeline_widget.main_track.clips[0] if self.timeline.timeline_widget.main_track.clips else None)) 
        # FIXME: The above lambda is hacky. We should pass the clip or just refresh.
        # Better: Inspector.refresh()
        
        # Let's add a refresh method to Inspector or just re-call set_clip with current
        self.player.transform_changed.connect(lambda: self.inspector.set_clip(self.player.current_clip))

    def open_export_dialog(self):
        from ..dialogs.export_dialog import ExportDialog
        dialog = ExportDialog(self)
        dialog.exec()
