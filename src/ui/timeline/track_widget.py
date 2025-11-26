from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, QSize, pyqtSignal
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
        self.setStyleSheet("#track_widget { background-color: #252526; border-bottom: 1px solid #333; }")
        self.setFixedHeight(80)
        
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header (Track Name)
        header = QWidget()
        header.setFixedWidth(100)
        header.setStyleSheet("background-color: #1E1E1E; border-right: 1px solid #333;")
        header_layout = QVBoxLayout(header)
        header_layout.addWidget(QLabel(track.name))
        self.layout.addWidget(header)
        
        # Track Content Area (Scrollable implicitly via parent)
        self.content_area = QWidget()
        self.content_area.setObjectName("track_content")
        self.content_area.setStyleSheet("background-color: transparent;")
        self.content_layout = QHBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 5, 0, 5)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.layout.addWidget(self.content_area)
        
        self.refresh()

    def refresh(self):
        # Clear existing clips
        for i in reversed(range(self.content_layout.count())): 
            self.content_layout.itemAt(i).widget().setParent(None)
            
        # Add clips
        for clip in self.track.clips:
            widget = ClipWidget(clip)
            width = int(clip.length * self.pixels_per_second)
            widget.setFixedSize(width, 70)
            widget.clicked.connect(self.on_clip_clicked)
            self.content_layout.addWidget(widget)
            
        self.content_layout.addStretch()

    def on_clip_clicked(self, clip_widget):
        self.clip_selected.emit(clip_widget.clip)
