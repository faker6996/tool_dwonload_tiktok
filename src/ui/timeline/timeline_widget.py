from PyQt6.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from .track_widget import TrackWidget
from src.core.timeline.track import MagneticTrack, Track
from src.core.timeline.clip import Clip
from src.core.commands.timeline_commands import AddClipCommand
from src.core.history import history_manager
import os

class RulerWidget(QWidget):
    def __init__(self, pixels_per_second=20):
        super().__init__()
        self.setFixedHeight(30)
        self.pixels_per_second = pixels_per_second
        self.setStyleSheet("background-color: #18181b; border-bottom: 1px solid #27272a;")
        self.playhead_time = 0.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor("#a1a1aa"))
        painter.setFont(QFont("Inter", 8))
        
        rect = self.rect()
        # Draw background
        painter.fillRect(rect, QColor("#18181b"))
        
        # Draw ticks
        start_x = 120 
        
        for i in range(0, 100): 
            x = start_x + (i * self.pixels_per_second)
            if x > rect.width():
                break
                
            if i % 5 == 0:
                painter.drawLine(x, 15, x, 30)
                painter.drawText(x + 2, 12, f"00:{i:02d}")
            else:
                painter.drawLine(x, 22, x, 30)
                
        # Draw bottom border
        painter.setPen(QColor("#27272a"))
        painter.drawLine(0, 29, rect.width(), 29)

        # Draw playhead indicator & time label
        start_x = 120
        x = start_x + int(self.playhead_time * self.pixels_per_second)
        if 0 <= x <= rect.width():
            painter.setPen(QColor("#6366f1"))
            painter.drawLine(x, 0, x, rect.height())
            painter.drawText(x + 4, rect.height() - 4, self._format_time(self.playhead_time))

    def _format_time(self, seconds: float) -> str:
        s = int(seconds) % 60
        m = int(seconds) // 60
        return f"{m:02d}:{s:02d}"

    def set_playhead_time(self, time_seconds: float):
        self.playhead_time = max(0.0, time_seconds)
        self.update()


class TimelineScrollArea(QScrollArea):
    """
    Custom scroll area that forwards wheel events to TimelineWidget so we
    can use the mouse wheel for zooming when hovering the timeline area.
    """

    def wheelEvent(self, event):
        parent = self.parent()
        while parent:
            if hasattr(parent, "handle_timeline_wheel"):
                parent.handle_timeline_wheel(event)
                return
            parent = parent.parent()
        super().wheelEvent(event)

class TimelineWidget(QFrame):
    """
    Main Timeline Widget.
    Manages multiple TrackWidgets.
    """
    clip_selected = pyqtSignal(object) # Emits Clip object or None

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self.setAcceptDrops(True)
        self.pixels_per_second = 20
        self.zoom_value = 20
        self.playhead_time = 0.0
        self.zoom_value = 20
        
        # Data
        self.main_track = MagneticTrack("Main Track")
        self.tracks = [self.main_track]
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Ruler
        self.ruler = RulerWidget(self.pixels_per_second)
        layout.addWidget(self.ruler)
        
        # Scroll Area for Tracks (horizontal scroll enabled)
        scroll = TimelineScrollArea(self)
        # Do NOT use setWidgetResizable(True) here, otherwise the
        # timeline content is forced to the viewport width and we
        # can't scroll for long videos.
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Enable vertical scroll for multiple tracks
        scroll.setStyleSheet("border: none; background-color: #131315;")
        
        self.tracks_container = QWidget()
        self.tracks_container.setStyleSheet("background-color: #131315;")
        self.tracks_layout = QVBoxLayout(self.tracks_container)
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        self.tracks_layout.setSpacing(1)
        self.tracks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.tracks_container)
        layout.addWidget(scroll)

        self.scroll = scroll
        
        # Playhead (Overlay)
        self.playhead = QFrame(self.tracks_container)
        self.playhead.setFixedWidth(2)
        self.playhead.setStyleSheet("background-color: #ef4444;")
        self.playhead.move(120, 0) # Start at 0s (offset by header)
        self.playhead.resize(2, 1000) # Tall enough
        self.playhead.show()
        self.playhead.raise_()
        
        self.refresh_tracks()

    def refresh_tracks(self):
        # Clear existing track widgets
        for i in reversed(range(self.tracks_layout.count())):
            item = self.tracks_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
            
        # Add track widgets
        for track in self.tracks:
            widget = TrackWidget(track, self.pixels_per_second)
            widget.clip_selected.connect(self.on_clip_selected)
            self.tracks_layout.addWidget(widget)

        # Update container size for proper scrolling
        self._update_timeline_width()
        
        # Update height based on number of tracks (each track is 90px)
        track_height = 90
        total_height = max(200, len(self.tracks) * track_height + 20)
        self.tracks_container.setMinimumHeight(total_height)
        
        print(f"Timeline refreshed: {len(self.tracks)} tracks")

    def on_clip_selected(self, clip):
        self.clip_selected.emit(clip)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls()]
            for file_path in files:
                self.add_clip_from_file(file_path)

    def add_text_clip(self, text: str, duration: float = 3.0):
        """
        Add a simple text clip to the main track.
        """
        clip = Clip(
            asset_id="text_generated",
            name=text,
            duration=duration,
            clip_type="text",
            text_content=text,
        )

        # Insert at current playhead time on the main track
        position = max(0.0, getattr(self, "playhead_time", 0.0))
        cmd = AddClipCommand(self.main_track, clip, position)
        history_manager.execute(cmd)

        self.refresh_tracks()
        self.playhead.raise_()

        # Notify listeners (Player/Inspector) so the newly added
        # text clip becomes the active/visible selection.
        self.clip_selected.emit(clip)

    def add_clip_from_file(self, file_path):
        # Lookup in StateManager to get metadata (duration, waveform)
        from src.core.state import state_manager
        
        # Find asset by path
        asset = None
        if hasattr(state_manager, "state") and "media_pool" in state_manager.state:
             for a in state_manager.state["media_pool"]["assets"].values():
                if a["target_url"] == file_path:
                    asset = a
                    break
        
        duration = 5.0
        waveform_path = None
        
        if asset:
            duration = asset["metadata"].get("duration", 5.0)
            waveform_path = asset["metadata"].get("waveformPath")
        
        clip = Clip(
            asset_id=file_path, # Using path as ID for now
            name=os.path.basename(file_path),
            duration=duration,
            waveform_path=waveform_path
        )
        
        # Use Command for Undo/Redo
        cmd = AddClipCommand(self.main_track, clip)
        history_manager.execute(cmd)
        
        # Refresh UI
        self.refresh_tracks()
        
        # Bring playhead to front
        self.playhead.raise_()

    def add_subtitle_track(self, segments, start_offset=0.0):
        """
        Create a new track for subtitles and add clips.
        Clears existing subtitle track first.
        """
        # Remove existing subtitle tracks first
        self.tracks = [t for t in self.tracks if t.name != "Subtitles"]
        
        subtitle_track = Track("Subtitles")
        self.tracks.append(subtitle_track)
        
        for seg in segments:
            start = seg["start"]
            end = seg["end"]
            text = seg["text"]
            duration = end - start
            
            clip = Clip(
                asset_id="text_generated",
                name=text,
                duration=duration,
                start_time=start_offset + start,
                clip_type="text",
                text_content=text
            )
            subtitle_track.clips.append(clip)
            
        self.refresh_tracks()
        self.playhead.raise_()
    
    def set_zoom(self, value):
        # Value 1-100
        # Map to pixels_per_second 5 - 100
        self.zoom_value = max(1, min(100, int(value)))
        self.pixels_per_second = max(5, self.zoom_value)
        self.ruler.pixels_per_second = self.pixels_per_second
        self.ruler.update()
        self.refresh_tracks()
        self.playhead.raise_()

    def set_playhead_time(self, time_seconds: float):
        """
        Move the red playhead to match a time on the main timeline.
        time_seconds is absolute timeline time (0 at start of main track).
        """
        if time_seconds < 0:
            time_seconds = 0
        self.playhead_time = time_seconds
        x = 120 + int(time_seconds * self.pixels_per_second)
        # Keep the playhead within a reasonable visible range
        x = max(0, x)
        self.playhead.move(x, 0)
        self.playhead.raise_()
        self.ruler.set_playhead_time(time_seconds)

    def _update_timeline_width(self):
        """
        Ensure the tracks container is wide enough to display all clips
        in the main track, so long videos can be scrolled horizontally.
        """
        # Base width so empty timelines still look reasonable
        min_width = 120 + int(60 * self.pixels_per_second)  # 60s default

        max_end = 0.0
        for track in self.tracks:
            for clip in track.clips:
                end_time = clip.start_time + clip.length
                if end_time > max_end:
                    max_end = end_time

        if max_end > 0:
            min_width = 120 + int(max_end * self.pixels_per_second) + 200

        self.tracks_container.setMinimumWidth(min_width)

    def handle_timeline_wheel(self, event):
        """
        Use mouse wheel over the timeline area to zoom in/out.
        """
        delta = event.angleDelta().y()
        if delta == 0:
            return

        step = 5
        direction = 1 if delta > 0 else -1
        new_zoom = self.zoom_value + direction * step
        new_zoom = max(1, min(100, new_zoom))
        if new_zoom == self.zoom_value:
            return

        self.set_zoom(new_zoom)
        event.accept()
