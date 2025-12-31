from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon
from .clip_widget import ClipWidget
from src.core.timeline.track import Track

class TrackWidget(QFrame):
    """
    Visual representation of a Track.
    Contains ClipWidgets.
    """
    clip_selected = pyqtSignal(object) # Emits Clip object
    playhead_seek = pyqtSignal(float) # Emits timeline time in seconds
    track_audio_changed = pyqtSignal() # Emits when track audio state changes

    def __init__(self, track: Track, pixels_per_second=20):
        super().__init__()
        self.track = track
        self.pixels_per_second = pixels_per_second
        self.setObjectName("track_widget")
        self.setStyleSheet("#track_widget { background-color: #121212; border-bottom: 1px solid #2C2C2C; }")
        self.setFixedHeight(90)
        
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header (Track Name + Controls)
        header = QWidget()
        header.setFixedWidth(120)
        header.setStyleSheet("background-color: #1E1E1E; border-right: 1px solid #2C2C2C;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(5)
        
        # Track Name
        self.name_label = QLabel(track.name)
        self.name_label.setStyleSheet("color: #E0E0E0; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.name_label)
        
        # Controls (Mute, Lock, Hide)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        self.mute_btn = self.create_icon_button("mute", "Mute")
        self.lock_btn = self.create_icon_button("lock", "Lock")
        self.hide_btn = self.create_icon_button("eye", "Hide")

        self.mute_btn.setChecked(getattr(self.track, "is_muted", False))
        self.lock_btn.setChecked(self.track.is_locked)
        self.hide_btn.setChecked(self.track.is_hidden)

        self.mute_btn.toggled.connect(self.on_mute_toggled)
        self.lock_btn.toggled.connect(self.on_lock_toggled)
        self.hide_btn.toggled.connect(self.on_hide_toggled)
        
        controls_layout.addWidget(self.mute_btn)
        controls_layout.addWidget(self.lock_btn)
        controls_layout.addWidget(self.hide_btn)
        controls_layout.addStretch()
        
        header_layout.addLayout(controls_layout)
        header_layout.addStretch()
        
        self.layout.addWidget(header)
        
        # Track Content Area - Use absolute positioning for clips!
        self.content_area = QWidget()
        self.content_area.setObjectName("track_content")
        self.content_area.setStyleSheet("background-color: #121212;")
        # NO layout manager - we'll use absolute positioning
        
        self.layout.addWidget(self.content_area)

        self.hidden_label = QLabel("Hidden", self.content_area)
        self.hidden_label.setStyleSheet("color: #71717a; font-size: 12px; padding-left: 12px;")
        self.hidden_label.move(0, 35)
        self.hidden_label.hide()
        
        self.refresh()

    def create_icon_button(self, icon_name, tooltip):
        btn = QPushButton()
        # btn.setIcon(QIcon(f"assets/icons/{icon_name}.png")) # Placeholder
        btn.setFixedSize(16, 16)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Style as a simple colored dot/icon for now since we don't have assets
        color = "#8b9dc3"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #E0E0E0;
            }}
            QPushButton:checked {{
                background-color: #EF4444; /* Red for active state like Mute */
            }}
        """)
        btn.setCheckable(True)
        return btn

    def refresh(self):
        self.update_state_ui()

        if self.track.is_hidden:
            self.content_area.setVisible(True)
        else:
            self.content_area.setVisible(True)

        # Clear existing clips (delete child widgets of content_area)
        for child in self.content_area.findChildren(ClipWidget):
            child.setParent(None)
            child.deleteLater()
        
        # Sort clips by start_time
        sorted_clips = sorted(self.track.clips, key=lambda c: c.start_time)
        
        # Calculate max end time for content area width
        max_end_time = 0.0
        for clip in sorted_clips:
            end_time = clip.start_time + clip.length
            if end_time > max_end_time:
                max_end_time = end_time
        
        # Set content area minimum width
        min_width = max(500, int(max_end_time * self.pixels_per_second) + 100)
        self.content_area.setMinimumWidth(min_width)

        if self.track.is_hidden:
            self.hidden_label.show()
            return
        self.hidden_label.hide()
        
        # Position clips using ABSOLUTE POSITIONING (not layout!)
        for clip in sorted_clips:
            widget = ClipWidget(clip)
            widget.setParent(self.content_area)
            
            # Calculate position and size
            x_pos = int(clip.start_time * self.pixels_per_second)
            width = max(30, int(clip.length * self.pixels_per_second))  # Min width 30px
            
            # Move clip to correct position (absolute positioning)
            widget.move(x_pos, 5)  # 5px top padding
            widget.setFixedSize(width, 80)
            widget.clicked.connect(self.on_clip_clicked)
            widget.clicked_at.connect(self.on_clip_clicked_at)
            widget.show()

    def update_state_ui(self):
        muted = getattr(self.track, "is_muted", False)
        if self.mute_btn.isChecked() != muted:
            self.mute_btn.setChecked(muted)
        if self.lock_btn.isChecked() != self.track.is_locked:
            self.lock_btn.setChecked(self.track.is_locked)
        if self.hide_btn.isChecked() != self.track.is_hidden:
            self.hide_btn.setChecked(self.track.is_hidden)

        if self.track.is_hidden:
            self.name_label.setStyleSheet("color: #71717a; font-weight: bold; font-size: 12px;")
        else:
            self.name_label.setStyleSheet("color: #E0E0E0; font-weight: bold; font-size: 12px;")

    def on_mute_toggled(self, checked: bool):
        self.track.is_muted = checked
        for clip in self.track.clips:
            clip.muted = checked
        self.update_state_ui()
        self.track_audio_changed.emit()

    def on_lock_toggled(self, checked: bool):
        self.track.is_locked = checked
        self.update_state_ui()

    def on_hide_toggled(self, checked: bool):
        self.track.is_hidden = checked
        self.refresh()

    def on_clip_clicked(self, clip_widget):
        self.clip_selected.emit(clip_widget.clip)

    def on_clip_clicked_at(self, clip_widget, local_x: float):
        width = max(1, clip_widget.width())
        ratio = max(0.0, min(1.0, local_x / width))
        time_seconds = clip_widget.clip.start_time + (clip_widget.clip.length * ratio)
        self.playhead_seek.emit(time_seconds)
