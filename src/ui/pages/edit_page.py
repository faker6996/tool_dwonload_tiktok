from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTabWidget, QLabel, QFrame, QToolButton, QButtonGroup, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta

from ..panels.media_pool import MediaPool
from ..panels.player import Player
from ..panels.inspector import Inspector
from ..panels.timeline import Timeline
from ..panels.effects import Effects
from ..panels.text_panel import TextPanel

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
        self.text_panel = TextPanel()
        
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
            timeline_widget = self.timeline.timeline_widget
            timeline_widget.clip_selected.connect(self.inspector.set_clip)
            timeline_widget.clip_selected.connect(self.player.set_clip)
            # Add text clips to main track
            self.text_panel.add_text_clip.connect(timeline_widget.add_text_clip)

            # Apply visual effects presets to the currently selected clip
            self.effects.effect_selected.connect(self.on_effect_selected)
            
            # Connect sticker signals
            self.effects.sticker_added.connect(self.on_sticker_added)

            # Sync player playback position to timeline playhead
            self.player.playhead_changed.connect(timeline_widget.set_playhead_time)

        self.inspector.clip_changed.connect(self.player.update_overlay)
        self.player.transform_changed.connect(lambda: self.inspector.set_clip(self.player.current_clip))
        if hasattr(self.inspector, "aspect_ratio_changed"):
            self.inspector.aspect_ratio_changed.connect(self.player.set_aspect_ratio)

    def on_effect_selected(self, name: str):
        """
        Apply a simple color preset to the currently selected clip.
        For now this only updates clip properties; Player/export can
        interpret these values as needed.
        """
        clip = getattr(self.player, "current_clip", None)
        if not clip:
            return

        # Basic preset mapping
        presets = {
            "Sepia":     {"brightness": 0.0, "contrast": 1.1, "saturation": 0.8, "hue": 25.0},
            "B&W":       {"brightness": 0.0, "contrast": 1.0, "saturation": 0.0, "hue": 0.0},
            "Vivid":     {"brightness": 0.0, "contrast": 1.2, "saturation": 1.5, "hue": 0.0},
            "Cool":      {"brightness": 0.0, "contrast": 1.0, "saturation": 1.0, "hue": -15.0},
            "Warm":      {"brightness": 0.0, "contrast": 1.0, "saturation": 1.0, "hue": 15.0},
            "Vintage":   {"brightness": -0.1, "contrast": 0.9, "saturation": 0.7, "hue": 20.0},
        }

        preset = presets.get(name)
        if not preset:
            # Unknown or custom filter, just store name
            clip.filter_name = name
            return

        clip.filter_name = name
        clip.brightness = preset["brightness"]
        clip.contrast = preset["contrast"]
        clip.saturation = preset["saturation"]
        clip.hue = preset["hue"]

        # Refresh player view with updated clip (if needed later)
        self.player.update_overlay(clip)

    def on_sticker_added(self, sticker_data: dict):
        """Handle sticker click from Effects panel - add to player canvas."""
        self.player.add_sticker(sticker_data)

    def open_export_dialog(self):
        from ..dialogs.export_dialog import ExportDialog
        dialog = ExportDialog(self)
        dialog.exec()
