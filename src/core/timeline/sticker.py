from dataclasses import dataclass, field
import uuid
from typing import Optional

@dataclass
class StickerClip:
    """
    Represents a sticker overlay on the timeline.
    """
    name: str
    sticker_type: str  # "emoji", "shape", "arrow", "custom"
    content: str  # Emoji character or asset path
    duration: float = 5.0  # Default 5 seconds
    start_time: float = 0.0  # Position on timeline
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Transform Properties
    position_x: float = 0.0  # Offset from center
    position_y: float = 0.0
    scale: float = 1.0
    rotation: float = 0.0
    opacity: float = 1.0
    
    # Optional asset path for image stickers
    asset_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "sticker_type": self.sticker_type,
            "content": self.content,
            "duration": self.duration,
            "start_time": self.start_time,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "scale": self.scale,
            "rotation": self.rotation,
            "opacity": self.opacity,
            "asset_path": self.asset_path,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "StickerClip":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Sticker"),
            sticker_type=data.get("sticker_type", "emoji"),
            content=data.get("content", "😀"),
            duration=data.get("duration", 5.0),
            start_time=data.get("start_time", 0.0),
            position_x=data.get("position_x", 0.0),
            position_y=data.get("position_y", 0.0),
            scale=data.get("scale", 1.0),
            rotation=data.get("rotation", 0.0),
            opacity=data.get("opacity", 1.0),
            asset_path=data.get("asset_path"),
        )
