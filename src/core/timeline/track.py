from typing import List, Optional
from .clip import Clip

class Track:
    """
    Base class for a timeline track.
    Manages a list of clips.
    """
    def __init__(self, name: str = "Track", is_audio: bool = False):
        self.name = name
        self.is_audio = is_audio
        self.clips: List[Clip] = []
        self.is_muted = False
        self.is_locked = False
        self.is_hidden = False

    def add_clip(self, clip: Clip, position: Optional[float] = None) -> bool:
        """
        Add a clip to the track.
        If position is None, append to end.
        Returns True if successful.
        """
        if self.is_locked:
            return False
            
        if position is not None:
            clip.start_time = position
        else:
            # Append to end
            if self.clips:
                last_clip = self.clips[-1]
                clip.start_time = last_clip.start_time + last_clip.length
            else:
                clip.start_time = 0.0
                
        self.clips.append(clip)
        self.clips.sort(key=lambda c: c.start_time) # Keep sorted by time
        return True

    def remove_clip(self, clip_id: str) -> Optional[Clip]:
        """
        Remove a clip by ID.
        Returns the removed clip or None.
        """
        if self.is_locked:
            return None
            
        for i, clip in enumerate(self.clips):
            if clip.id == clip_id:
                return self.clips.pop(i)
        return None

class MagneticTrack(Track):
    """
    Main Track with Magnetic Timeline logic.
    Clips automatically snap together. Deleting a clip ripples subsequent clips.
    """
    def __init__(self, name: str = "Main Track"):
        super().__init__(name, is_audio=False)

    def add_clip(self, clip: Clip, position: Optional[float] = None) -> bool:
        """
        Add clip and ripple shift subsequent clips if inserted.
        For MVP, we mainly support appending or simple insertion.
        """
        if self.is_locked:
            return False

        # In magnetic track, position is less strict. 
        # If position is provided, we might split or insert.
        # For simple append:
        if position is None or not self.clips:
            return super().add_clip(clip)
            
        # Insertion logic (simplified for MVP)
        # Find insertion index
        insert_index = 0
        for i, c in enumerate(self.clips):
            if c.start_time > position:
                insert_index = i
                break
            insert_index = i + 1
            
        # Shift subsequent clips
        shift_amount = clip.length
        for i in range(insert_index, len(self.clips)):
            self.clips[i].start_time += shift_amount
            
        clip.start_time = position # Ideally should snap to previous clip end
        # Snap logic:
        if insert_index > 0:
            prev_clip = self.clips[insert_index - 1]
            clip.start_time = prev_clip.start_time + prev_clip.length
            
        self.clips.insert(insert_index, clip)
        return True

    def remove_clip(self, clip_id: str) -> Optional[Clip]:
        """
        Remove clip and ripple delete (shift subsequent clips back).
        """
        if self.is_locked:
            return None
            
        removed_clip = None
        remove_index = -1
        
        for i, clip in enumerate(self.clips):
            if clip.id == clip_id:
                removed_clip = clip
                remove_index = i
                break
                
        if removed_clip:
            self.clips.pop(remove_index)
            # Ripple shift back
            shift_amount = removed_clip.length
            for i in range(remove_index, len(self.clips)):
                self.clips[i].start_time -= shift_amount
                
        return removed_clip


class StickerTrack(Track):
    """
    Track for sticker overlays.
    Stickers can overlap and are not magnetic.
    """
    def __init__(self, name: str = "Stickers"):
        super().__init__(name, is_audio=False)
        self.stickers = []  # List of StickerClip objects
    
    def add_sticker(self, sticker, position: Optional[float] = None) -> bool:
        """
        Add a sticker to the track.
        """
        if self.is_locked:
            return False
        
        if position is not None:
            sticker.start_time = position
        
        self.stickers.append(sticker)
        self.stickers.sort(key=lambda s: s.start_time)
        return True
    
    def remove_sticker(self, sticker_id: str):
        """
        Remove a sticker by ID.
        """
        if self.is_locked:
            return None
        
        for i, sticker in enumerate(self.stickers):
            if sticker.id == sticker_id:
                return self.stickers.pop(i)
        return None
    
    def get_stickers_at_time(self, time: float) -> list:
        """
        Get all stickers visible at a specific time.
        """
        return [
            s for s in self.stickers
            if s.start_time <= time < s.start_time + s.duration
        ]
