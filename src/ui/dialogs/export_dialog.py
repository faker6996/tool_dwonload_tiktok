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
        self.res_combo.addItems(["1920x1080", "1280x720", "3840x2160"])
        settings_layout.addWidget(self.res_combo)
        
        # FPS
        settings_layout.addWidget(QLabel("FPS:"))
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["30", "60", "24"])
        settings_layout.addWidget(self.fps_combo)
        
        layout.addLayout(settings_layout)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.start_export)
        self.export_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
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

        settings = {
            "resolution": self.res_combo.currentText(),
            "fps": int(self.fps_combo.currentText())
        }
        
        # UI State
        self.export_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # Start Render
        render_engine.render_timeline(timeline_clips, output_path, settings)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_render_finished(self, success, message):
        self.export_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        if success:
            self.progress_bar.setFormat("Done!")
            QMessageBox.information(self, "Export Video", message or "Export finished.")
            # Optionally close dialog on success
            # self.accept()
        else:
            self.progress_bar.setFormat("Error")
            QMessageBox.critical(self, "Export Video", message or "Export failed.")
