from __future__ import annotations

import os
import tempfile
from typing import Optional

from .planner import ExportSubtitlePlan


def create_ass_subtitle_file(
    subtitles: list[ExportSubtitlePlan],
    video_width: int,
    video_height: int,
) -> Optional[str]:
    if not subtitles:
        return None

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,56,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,2,2,20,20,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    for subtitle in subtitles:
        text = subtitle.text_content.strip()
        if not text:
            continue

        start_time = subtitle.start_time
        end_time = start_time + subtitle.duration
        escaped_text = _escape_ass_text(text)
        events.append(
            f"Dialogue: 0,{format_ass_time(start_time)},{format_ass_time(end_time)},Default,,0,0,0,,{escaped_text}"
        )

    if not events:
        return None

    subtitle_fd, subtitle_path = tempfile.mkstemp(
        suffix=".ass",
        prefix="subtitles_",
        text=True,
    )
    with os.fdopen(subtitle_fd, "w", encoding="utf-8") as subtitle_file:
        subtitle_file.write(ass_header)
        subtitle_file.write("\n".join(events))

    return subtitle_path


def format_ass_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    whole_seconds = int(seconds % 60)
    centiseconds = int((seconds * 100) % 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{centiseconds:02d}"


def _escape_ass_text(text: str) -> str:
    escaped_text = text.replace("\\", "/").replace("{", "\\{").replace("}", "\\}")
    return escaped_text.replace("\n", "\\N")
