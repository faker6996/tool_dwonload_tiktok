from __future__ import annotations

import subprocess
from typing import Optional


def get_source_resolution(video_path: str) -> Optional[tuple[int, int]]:
    if not video_path:
        return None
    try:
        import cv2  # type: ignore
    except Exception:
        return None

    capture = cv2.VideoCapture(video_path)
    try:
        if not capture.isOpened():
            return None
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        if width > 0 and height > 0:
            return width, height
        return None
    finally:
        capture.release()


def source_has_audio(video_path: str, ffmpeg_path: str) -> bool:
    if not video_path:
        return False
    try:
        probe = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-i", video_path],
            capture_output=True,
            text=True,
        )
        probe_output = (probe.stderr or "") + (probe.stdout or "")
        return "Audio:" in probe_output
    except Exception:
        return False
