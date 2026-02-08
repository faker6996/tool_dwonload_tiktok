from copy import deepcopy
from typing import List, Optional
import uuid
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

    def get_clip_index(self, clip_id: str) -> int:
        for index, clip in enumerate(self.clips):
            if clip.id == clip_id:
                return index
        return -1

    def get_clip(self, clip_id: str) -> Optional[Clip]:
        index = self.get_clip_index(clip_id)
        if index < 0:
            return None
        return self.clips[index]

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

    def split_clip(self, clip_id: str, timeline_time: float) -> Optional[Clip]:
        """
        Split a clip at absolute timeline time and insert right-side clip.
        Returns the new right-side clip, or None if invalid.
        """
        if self.is_locked:
            return None

        clip_index = self.get_clip_index(clip_id)
        if clip_index < 0:
            return None

        clip = self.clips[clip_index]
        clip_start = clip.start_time
        clip_end = clip.start_time + clip.length

        if timeline_time <= clip_start or timeline_time >= clip_end:
            return None

        media_split_point = clip.in_point + (timeline_time - clip_start)
        if media_split_point <= clip.in_point or media_split_point >= clip.out_point:
            return None

        right_clip = deepcopy(clip)
        right_clip.id = str(uuid.uuid4())
        right_clip.start_time = timeline_time
        right_clip.in_point = media_split_point

        clip.out_point = media_split_point
        self.clips.insert(clip_index + 1, right_clip)
        return right_clip

    def trim_clip(
        self,
        clip_id: str,
        new_in_point: Optional[float] = None,
        new_out_point: Optional[float] = None,
    ) -> bool:
        """
        Trim clip in/out and ripple shift subsequent clips by length delta.
        Returns True on success.
        """
        if self.is_locked:
            return False

        clip_index = self.get_clip_index(clip_id)
        if clip_index < 0:
            return False

        clip = self.clips[clip_index]
        current_in = clip.in_point
        current_out = clip.out_point

        target_in = current_in if new_in_point is None else float(new_in_point)
        target_out = current_out if new_out_point is None else float(new_out_point)

        target_in = max(0.0, min(target_in, clip.duration))
        target_out = max(0.0, min(target_out, clip.duration))

        if target_out <= target_in:
            return False

        old_length = clip.length
        clip.in_point = target_in
        clip.out_point = target_out
        length_delta = clip.length - old_length

        if abs(length_delta) > 1e-9:
            for i in range(clip_index + 1, len(self.clips)):
                self.clips[i].start_time += length_delta

        return True


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
