from .base import Command
from ..timeline.track import Track
from ..timeline.clip import Clip

class AddClipCommand(Command):
    def __init__(self, track: Track, clip: Clip, position: float = None):
        self.track = track
        self.clip = clip
        self.position = position
        
    def execute(self):
        self.track.add_clip(self.clip, self.position)
        
    def undo(self):
        self.track.remove_clip(self.clip.id)

class RemoveClipCommand(Command):
    def __init__(self, track: Track, clip_id: str):
        self.track = track
        self.clip_id = clip_id
        self.removed_clip = None
        self.removed_position = 0.0
        
    def execute(self):
        # We need to find the clip first to know its position for undo
        for clip in self.track.clips:
            if clip.id == self.clip_id:
                self.removed_position = clip.start_time
                break
        self.removed_clip = self.track.remove_clip(self.clip_id)
        
    def undo(self):
        if self.removed_clip:
            self.track.add_clip(self.removed_clip, self.removed_position)
