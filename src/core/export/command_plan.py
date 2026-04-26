from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .planner import ExportPlan


@dataclass(frozen=True)
class OutputCommandPlan:
    size_args: list[str] = field(default_factory=list)
    fps_args: list[str] = field(default_factory=list)
    audio_codec_args: list[str] = field(default_factory=lambda: ["-c:a", "aac", "-b:a", "192k"])
    video_codec_args: list[str] = field(
        default_factory=lambda: [
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
        ]
    )


def build_output_command_plan(export_plan: ExportPlan) -> OutputCommandPlan:
    return OutputCommandPlan(
        size_args=_build_size_args(export_plan.settings.resolution),
        fps_args=_build_fps_args(export_plan.settings.fps),
    )


def _build_size_args(resolution: str) -> list[str]:
    if isinstance(resolution, str) and resolution.lower() == "original":
        return []
    return ["-s", str(resolution)]


def _build_fps_args(fps_setting: Any) -> list[str]:
    if isinstance(fps_setting, str) and fps_setting.lower() == "original":
        return []
    try:
        fps_value = float(fps_setting)
    except Exception:
        return ["-r", "30"]
    if fps_value > 0:
        return ["-r", str(fps_value)]
    return []
