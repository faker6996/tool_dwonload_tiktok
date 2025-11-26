from dataclasses import dataclass, field
import uuid
from typing import Optional

@dataclass
class Clip:
    """
    Represents a media clip on the timeline.
    """
    asset_id: str
    name: str
    duration: float # In seconds
    start_time: float = 0.0 # Position on timeline (seconds)
    in_point: float = 0.0 # Trim in (seconds)
    out_point: float = 0.0 # Trim out (seconds)
    track_index: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Transform Properties
    position_x: float = 0.0
    position_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0
    opacity: float = 1.0
    blend_mode: str = "Normal"
    
    # Audio Properties
    volume: float = 1.0 # 0.0 to 1.0 (or higher for boost)
    muted: bool = False
    fade_in: float = 0.0 # Seconds
    fade_out: float = 0.0 # Seconds
    waveform_path: Optional[str] = None
    
    # Text/Subtitle Properties
    clip_type: str = "video" # video, audio, text
    text_content: str = ""
    font_size: int = 24
    font_color: str = "#FFFFFF"
    
    # Color Correction Properties
    brightness: float = 0.0 # -1.0 to 1.0
    contrast: float = 1.0 # 0.0 to 2.0
    saturation: float = 1.0 # 0.0 to 2.0
    hue: float = 0.0 # -180 to 180
    
    # Performance
    proxy_path: Optional[str] = None
    
    def __post_init__(self):
        if self.out_point == 0.0:
            self.out_point = self.duration

    @property
    def length(self) -> float:
        """Effective length of the clip on timeline (out - in)."""
        return self.out_point - self.in_point
