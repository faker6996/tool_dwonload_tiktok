from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTabWidget, QLabel, QFrame, QToolButton, QButtonGroup, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta

from ..panels.media_pool import MediaPool
from ..panels.player import Player
from ..panels.inspector import Inspector
from ..panels.timeline import Timeline
from ..panels.effects import Effects

class EditPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main Vertical Splitter (Top: Workspace, Bottom: Timeline)
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.setHandleWidth(1)
        main_splitter.setChildrenCollapsible(False)

        # Top Horizontal Splitter (Nav | Media | Player | Inspector)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.setHandleWidth(1)
        top_splitter.setChildrenCollapsible(False)

        # 2. Media Panel (Tabs)
        self.left_panel = QTabWidget()
        self.left_panel.setMinimumWidth(300)
        
        self.media_pool = MediaPool()
        self.effects = Effects()
        self.text_panel = QWidget() # Placeholder
        
        self.left_panel.addTab(self.media_pool, "Media")
        self.left_panel.addTab(self.effects, "Effects")
        self.left_panel.addTab(self.text_panel, "Text")

        # 3. Center Panel (Player)
        self.player = Player()
        
        # 4. Right Panel (Inspector)
        self.inspector = Inspector()
        self.inspector.setMinimumWidth(300)

        # Add to Top Splitter
        top_splitter.addWidget(self.left_panel)
        top_splitter.addWidget(self.player)
        top_splitter.addWidget(self.inspector)

        # Set initial sizes for top splitter
        top_splitter.setStretchFactor(0, 3)  # Media
        top_splitter.setStretchFactor(1, 6)  # Player
        top_splitter.setStretchFactor(2, 3)  # Inspector

        # --- Bottom Panel (Timeline) ---
        self.timeline = Timeline()

        # Add to Main Splitter
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.timeline)

        # Set initial sizes for main splitter
        # Use a default ratio but ensure timeline is visible
        main_splitter.setStretchFactor(0, 6)
        main_splitter.setStretchFactor(1, 4)
        main_splitter.setSizes([500, 300]) # Explicitly set sizes to ensure visibility on load

        layout.addWidget(main_splitter)
        
        # Connect Signals
        if hasattr(self.timeline, 'timeline_widget'):
            self.timeline.timeline_widget.clip_selected.connect(self.inspector.set_clip)
            self.timeline.timeline_widget.clip_selected.connect(self.player.set_clip)

        self.inspector.clip_changed.connect(self.player.update_overlay)
        self.player.transform_changed.connect(lambda: self.inspector.set_clip(self.player.current_clip))
        if hasattr(self.inspector, "aspect_ratio_changed"):
            self.inspector.aspect_ratio_changed.connect(self.player.set_aspect_ratio)

    def open_export_dialog(self):
        from ..dialogs.export_dialog import ExportDialog
        dialog = ExportDialog(self)
        dialog.exec()
