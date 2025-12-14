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
        name_label = QLabel(track.name)
        name_label.setStyleSheet("color: #E0E0E0; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(name_label)
        
        # Controls (Mute, Lock, Hide)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        self.mute_btn = self.create_icon_button("mute", "Mute")
        self.lock_btn = self.create_icon_button("lock", "Lock")
        self.hide_btn = self.create_icon_button("eye", "Hide")
        
        controls_layout.addWidget(self.mute_btn)
        controls_layout.addWidget(self.lock_btn)
        controls_layout.addWidget(self.hide_btn)
        controls_layout.addStretch()
        
        header_layout.addLayout(controls_layout)
        header_layout.addStretch()
        
        self.layout.addWidget(header)
        
        # Track Content Area (Scrollable implicitly via parent)
        self.content_area = QWidget()
        self.content_area.setObjectName("track_content")
        self.content_area.setStyleSheet("background-color: #121212;")
        self.content_layout = QHBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 5, 0, 5)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.layout.addWidget(self.content_area)
        
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
        # Clear existing clips
        for i in reversed(range(self.content_layout.count())): 
            item = self.content_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            
        # Sort clips by start_time
        sorted_clips = sorted(self.track.clips, key=lambda c: c.start_time)
        
        # Position clips based on start_time
        for clip in sorted_clips:
            widget = ClipWidget(clip)
            width = max(30, int(clip.duration * self.pixels_per_second))  # Min width 30px
            
            # Calculate x position based on start_time
            x_pos = int(clip.start_time * self.pixels_per_second)
            
            # Set size
            widget.setFixedSize(width, 80)
            widget.clicked.connect(self.on_clip_clicked)
            
            # Add to layout at correct position using spacer
            self.content_layout.addWidget(widget)
            
        self.content_layout.addStretch()

    def on_clip_clicked(self, clip_widget):
        self.clip_selected.emit(clip_widget.clip)
