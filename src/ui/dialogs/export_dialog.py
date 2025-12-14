from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFileDialog,
    QProgressBar,
    QMessageBox,
    QWidget,
)
from PyQt6.QtCore import Qt
from src.core.export.renderer import render_engine

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Video")
        self.resize(500, 300)
        self.setup_ui()
        
        # Connect signals
        render_engine.progress_updated.connect(self.update_progress)
        render_engine.render_finished.connect(self.on_render_finished)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Output Path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Output Path:"))
        self.path_input = QLineEdit()
        path_layout.addWidget(self.path_input)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # Settings
        settings_layout = QHBoxLayout()
        
        # Resolution
        settings_layout.addWidget(QLabel("Resolution:"))
        self.res_combo = QComboBox()
        self.res_combo.addItems([
            "1080x1920 (TikTok/Reels)",  # Vertical
            "1920x1080 (Full HD)",        # Horizontal
            "720x1280 (HD Vertical)",     # Vertical
            "1280x720 (HD)",              # Horizontal
            "2160x3840 (4K Vertical)",    # Vertical
            "3840x2160 (4K)",             # Horizontal
        ])
        settings_layout.addWidget(self.res_combo)
        
        # FPS
        settings_layout.addWidget(QLabel("FPS:"))
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["30", "60", "24"])
        settings_layout.addWidget(self.fps_combo)
        
        layout.addLayout(settings_layout)
        
        # Progress Section
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 10, 0, 10)
        
        # Status label
        self.status_label = QLabel("Ready to export")
        self.status_label.setStyleSheet("color: #a1a1aa; font-size: 13px;")
        progress_layout.addWidget(self.status_label)
        
        # Progress Bar with percentage
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p% - Encoding...")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #27272a;
                border-radius: 5px;
                background-color: #18181b;
                height: 20px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 4px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Time estimate label
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #71717a; font-size: 11px;")
        progress_layout.addWidget(self.time_label)
        
        self.progress_container.hide()
        layout.addWidget(self.progress_container)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.start_export)
        self.export_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: bold; padding: 8px 20px;")
        btn_layout.addWidget(self.export_btn)
        
        layout.addLayout(btn_layout)

    def browse_path(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "Video Files (*.mp4 *.mov)")
        if path:
            self.path_input.setText(path)

    def start_export(self):
        output_path = self.path_input.text()
        if not output_path:
            QMessageBox.warning(self, "Export Video", "Please choose an output path.")
            return

        # Collect timeline clips from parent EditPage -> Timeline -> TimelineWidget
        timeline_clips = []
        parent = self.parent()
        try:
            if parent and hasattr(parent, "timeline"):
                timeline_panel = parent.timeline
                if hasattr(timeline_panel, "timeline_widget"):
                    timeline_widget = timeline_panel.timeline_widget
                    # For now we export only the main video track.
                    main_track = getattr(timeline_widget, "main_track", None)
                    if main_track and getattr(main_track, "clips", None):
                        for clip in main_track.clips:
                            timeline_clips.append(
                                {
                                    "path": clip.asset_id,
                                    "start": clip.start_time,
                                    "duration": clip.length,
                                    # Pass transform info for future use (e.g. blend modes)
                                    "blend_mode": getattr(clip, "blend_mode", "Normal"),
                                    "opacity": getattr(clip, "opacity", 1.0),
                                }
                            )
        except Exception as e:
            print(f"Error collecting timeline clips: {e}")

        if not timeline_clips:
            QMessageBox.warning(
                self,
                "Export Video",
                "Timeline is empty. Please add at least one clip before exporting.",
            )
            return

        # Collect stickers from Player canvas
        stickers_data = []
        try:
            if parent and hasattr(parent, "player"):
                player = parent.player
                if hasattr(player, "stickers"):
                    for sticker_item in player.stickers:
                        transform = sticker_item.get_transform_data()
                        stickers_data.append({
                            "content": sticker_item.content,
                            "type": sticker_item.sticker_type,
                            "x": transform.get("position_x", 0),
                            "y": transform.get("position_y", 0),
                            "scale": transform.get("scale", 1.0),
                            "rotation": transform.get("rotation", 0),
                            "opacity": transform.get("opacity", 1.0),
                        })
        except Exception as e:
            print(f"Error collecting stickers: {e}")

        # Collect subtitles from Subtitles track
        subtitles_data = []
        try:
            if parent and hasattr(parent, "timeline"):
                timeline_panel = parent.timeline
                if hasattr(timeline_panel, "timeline_widget"):
                    timeline_widget = timeline_panel.timeline_widget
                    # Find Subtitles track
                    for track in timeline_widget.tracks:
                        if track.name == "Subtitles":
                            for clip in track.clips:
                                if hasattr(clip, "text_content"):
                                    subtitles_data.append({
                                        "start_time": clip.start_time,
                                        "duration": clip.length,
                                        "text_content": clip.text_content or clip.name,
                                    })
                            print(f"Collected {len(subtitles_data)} subtitles for burning")
                            break
        except Exception as e:
            print(f"Error collecting subtitles: {e}")

        # Extract just resolution numbers (e.g. "1080x1920 (TikTok/Reels)" -> "1080x1920")
        resolution_text = self.res_combo.currentText()
        resolution = resolution_text.split(" ")[0]  # Get "1080x1920" from "1080x1920 (TikTok/Reels)"
        
        settings = {
            "resolution": resolution,
            "fps": int(self.fps_combo.currentText())
        }
        
        # UI State - show loading
        self.export_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel Export")
        self.progress_container.show()
        self.progress_bar.setValue(0)
        self.status_label.setText("🎬 Encoding video... Please wait, this may take several minutes.")
        self.status_label.setStyleSheet("color: #fbbf24; font-size: 13px; font-weight: bold;")
        self.time_label.setText("⏳ Video encoding in progress. Do not close this window.")
        
        # Store start time for duration estimate
        import time
        self._export_start_time = time.time()
        
        # Start Render (with stickers and subtitles)
        render_engine.render_timeline(timeline_clips, output_path, settings, stickers_data, subtitles_data)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
        # Update time estimate
        import time
        if hasattr(self, '_export_start_time') and value > 0:
            elapsed = time.time() - self._export_start_time
            if value < 100:
                estimated_total = elapsed / (value / 100)
                remaining = estimated_total - elapsed
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                self.time_label.setText(f"⏳ Estimated time remaining: {mins}m {secs}s")

    def on_render_finished(self, success, message):
        self.export_btn.setEnabled(True)
        self.cancel_btn.setText("Close")
        if success:
            self.status_label.setText("✅ Export completed successfully!")
            self.status_label.setStyleSheet("color: #22c55e; font-size: 13px; font-weight: bold;")
            self.progress_bar.setFormat("100% - Done!")
            self.time_label.setText("")
            QMessageBox.information(self, "Export Video", message or "Export finished successfully!")
        else:
            self.status_label.setText("❌ Export failed")
            self.status_label.setStyleSheet("color: #ef4444; font-size: 13px; font-weight: bold;")
            self.progress_bar.setFormat("Error")
            self.time_label.setText(message or "Unknown error")
            QMessageBox.critical(self, "Export Video", message or "Export failed.")

