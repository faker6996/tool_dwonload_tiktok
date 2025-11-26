from PyQt6.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from .track_widget import TrackWidget
from src.core.timeline.track import MagneticTrack
from src.core.timeline.clip import Clip
from src.core.commands.timeline_commands import AddClipCommand
from src.core.history import history_manager
import os

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
        
        # Data
        self.main_track = MagneticTrack("Main Track")
        self.tracks = [self.main_track]
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area for Tracks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.tracks_container = QWidget()
        self.tracks_layout = QVBoxLayout(self.tracks_container)
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        self.tracks_layout.setSpacing(1)
        self.tracks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.tracks_container)
        layout.addWidget(scroll)
        
        self.refresh_tracks()

    def refresh_tracks(self):
        # Clear existing track widgets
        for i in reversed(range(self.tracks_layout.count())):
            self.tracks_layout.itemAt(i).widget().setParent(None)
            
        # Add track widgets
        for track in self.tracks:
            widget = TrackWidget(track)
            widget.clip_selected.connect(self.on_clip_selected)
            self.tracks_layout.addWidget(widget)

    def on_clip_selected(self, clip):
        self.clip_selected.emit(clip)
        # Ideally we should also deselect other clips in other tracks/widgets
        # For now, let's just emit.

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Check if dropping from Media Pool (Asset ID)
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            # This is complex to parse directly from QListWidget default mime type.
            # But we set custom mime data in MediaPool? No, we enabled default drag.
            # Let's check if we can get text which might be the ID if we set it?
            # Actually MediaPool uses default drag.
            # Let's assume for now we handle file drops primarily.
            # To handle MediaPool drops properly, we should subclass QListWidget in MediaPool 
            # or handle the mime data better.
            
            # Workaround: If we can't easily get the ID, we might need to rely on file paths 
            # if the drag contains them. QListWidget drags usually don't contain file URLs unless set.
            pass
            
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls()]
            for file_path in files:
                self.add_clip_from_file(file_path)

    def add_clip_from_file(self, file_path):
        # Lookup in StateManager to get metadata (duration, waveform)
        from src.core.state import state_manager
        
        # Find asset by path
        asset = None
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

    def add_subtitle_track(self, segments, start_offset=0.0):
        """
        Create a new track for subtitles and add clips.
        """
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
