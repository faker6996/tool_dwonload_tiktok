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
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # Main Vertical Splitter (Top: Workspace, Bottom: Timeline)
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.setHandleWidth(2)
        main_splitter.setChildrenCollapsible(False)

        # Top Horizontal Splitter (Left Panel | Player | Inspector)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.setHandleWidth(2)
        top_splitter.setChildrenCollapsible(False)

        # Left Panel (Tabs: Media Pool, Effects)
        from PyQt6.QtWidgets import QTabWidget
        from ..panels.effects import Effects
        
        self.left_panel = QTabWidget()
        self.left_panel.setMinimumWidth(260)
        self.left_panel.setStyleSheet("""
            QTabWidget::pane { 
                border: none; 
            }
            QTabBar::tab { 
                background: #1E1E1E; 
                color: #BBB; 
                padding: 6px 14px; 
                font-size: 12px;
            }
            QTabBar::tab:selected { 
                background: #2C2C2C; 
                color: #FFF; 
            }
        """)
        
        self.media_pool = MediaPool()
        self.effects = Effects()
        
        self.left_panel.addTab(self.media_pool, "Media")
        self.left_panel.addTab(self.effects, "Effects")

        self.player = Player()
        self.inspector = Inspector()
        self.inspector.setMinimumWidth(260)
        self.timeline = Timeline()

        # Add to Top Splitter
        top_splitter.addWidget(self.left_panel)
        top_splitter.addWidget(self.player)
        top_splitter.addWidget(self.inspector)

        # Set initial sizes for top splitter (20% | 60% | 20%)
        # Note: We can't set exact pixels easily without window size, 
        # but we can set stretch factors or initial sizes if we knew the width.
        # For now, let's rely on default or setStretchFactor.
        # Give priority to the player area, keep media/inspector compact
        top_splitter.setStretchFactor(0, 2)  # Media Pool
        top_splitter.setStretchFactor(1, 5)  # Player
        top_splitter.setStretchFactor(2, 3)  # Inspector

        # Add to Main Splitter
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.timeline)

        # Set initial sizes for main splitter (70% Top | 30% Bottom)
        main_splitter.setStretchFactor(0, 7)
        main_splitter.setStretchFactor(1, 3)

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
