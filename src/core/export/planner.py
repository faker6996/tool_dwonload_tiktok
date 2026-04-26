from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from typing import Any, Optional

try:
    import video_core as _video_core
except ImportError:
    _video_core = None


@dataclass(frozen=True)
class ExportClipPlan:
    path: str
    start: float
    in_point: float
    out_point: Optional[float]
    duration: float


@dataclass(frozen=True)
class ExportPlanSettings:
    resolution: str = "1920x1080"
    fps: Any = 30
    speed: float = 1.0
    gap_policy: str = "omit"


@dataclass(frozen=True)
class ExportStickerPlan:
    content: str
    x: float = 0.0
    y: float = 0.0
    scale: float = 1.0


@dataclass(frozen=True)
class ExportSubtitlePlan:
    start_time: float
    duration: float
    text_content: str


@dataclass(frozen=True)
class ExportAudioPlan:
    path: str
    start_time: float = 0.0
    duration: float = 0.0


@dataclass(frozen=True)
class ExportFilterPlan:
    has_video_speed_filter: bool = False
    has_audio_speed_filter: bool = False
    has_subtitles: bool = False
    sticker_count: int = 0
    audio_track_count: int = 0
    needs_filter_complex: bool = False


@dataclass(frozen=True)
class ExportFilterStep:
    target: str
    kind: str
    value: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExportGapPlan:
    start: float
    duration: float
    policy: str = "omit"


@dataclass(frozen=True)
class ExportPlan:
    clips: list[ExportClipPlan]
    settings: ExportPlanSettings
    total_duration: float
    stickers: list[ExportStickerPlan] = field(default_factory=list)
    subtitles: list[ExportSubtitlePlan] = field(default_factory=list)
    audio_tracks: list[ExportAudioPlan] = field(default_factory=list)
    filters: ExportFilterPlan = field(default_factory=ExportFilterPlan)
    filter_steps: list[ExportFilterStep] = field(default_factory=list)
    gaps: list[ExportGapPlan] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def has_filter_step(self, target: str, kind: str) -> bool:
        return any(
            step.target == target and step.kind == kind for step in self.filter_steps
        )


def build_export_plan(
    clips: list[dict],
    settings: dict | None,
    stickers: list[dict] | None = None,
    subtitles: list[dict] | None = None,
    audio_tracks: list[dict] | None = None,
) -> ExportPlan:
    if _has_native_export_planner():
        return _build_native_export_plan(
            clips,
            settings or {},
            stickers or [],
            subtitles or [],
            audio_tracks or [],
        )
    return _build_python_export_plan(
        clips,
        settings or {},
        stickers or [],
        subtitles or [],
        audio_tracks or [],
    )


def _has_native_export_planner() -> bool:
    return _video_core is not None and hasattr(_video_core, "build_export_plan_full_json")


def _build_native_export_plan(
    clips: list[dict],
    settings: dict,
    stickers: list[dict],
    subtitles: list[dict],
    audio_tracks: list[dict],
) -> ExportPlan:
    plan_json = _video_core.build_export_plan_full_json(
        json.dumps(clips),
        json.dumps(settings),
        json.dumps(stickers),
        json.dumps(subtitles),
        json.dumps(audio_tracks),
    )
    plan_data = json.loads(plan_json)
    if (
        "filter_steps" not in plan_data
        or "gaps" not in plan_data
        or (
            _normalize_gap_policy(settings.get("gap_policy")) == "reject"
            and plan_data.get("gaps")
        )
    ):
        return _build_python_export_plan(
            clips,
            settings,
            stickers,
            subtitles,
            audio_tracks,
        )
    return _plan_from_dict(plan_data)


def _build_python_export_plan(
    clips: list[dict],
    settings: dict,
    stickers: list[dict],
    subtitles: list[dict],
    audio_tracks: list[dict],
) -> ExportPlan:
    warnings = []
    planned_clips = []

    for index, clip in enumerate(clips):
        path = str(clip.get("path") or "")
        if not path:
            warnings.append(f"Skipping clip {index}: missing path.")
            continue
        if not os.path.exists(path):
            warnings.append(f"Skipping missing clip path: {path}")
            continue

        in_point = max(0.0, _as_float(clip.get("in_point", 0.0), 0.0))
        duration = max(0.0, _as_float(clip.get("duration", 0.0), 0.0))
        out_point = _read_out_point(clip, in_point, duration)
        effective_duration = max(0.0, (out_point - in_point) if out_point else duration)

        if effective_duration <= 0.0:
            warnings.append(f"Skipping clip {index}: non-positive duration.")
            continue

        planned_clips.append(
            ExportClipPlan(
                path=path,
                start=_as_float(clip.get("start", 0.0), 0.0),
                in_point=in_point,
                out_point=out_point,
                duration=effective_duration,
            )
        )

    planned_clips.sort(key=lambda clip: clip.start)

    if not planned_clips:
        raise ValueError("No valid clip files to render.")

    gap_policy = _normalize_gap_policy(settings.get("gap_policy", "omit"))
    gaps = _plan_gaps(planned_clips, gap_policy, warnings)
    speed = _as_float(settings.get("speed", settings.get("export_speed", 1.0)), 1.0)
    if speed <= 0.0:
        speed = 1.0

    resolution = str(settings.get("resolution") or "1920x1080")
    fps = settings.get("fps", 30)
    total_duration = sum(clip.duration for clip in planned_clips) / speed
    planned_stickers = _plan_stickers(stickers, warnings)
    planned_subtitles = _plan_subtitles(subtitles, warnings)
    planned_audio_tracks = _plan_audio_tracks(audio_tracks, warnings)
    wants_speed_filter = abs(speed - 1.0) > 1e-6
    filter_steps = _plan_filter_steps(
        wants_speed_filter,
        len(planned_stickers),
        len(planned_subtitles),
        len(planned_audio_tracks),
        speed,
    )

    return ExportPlan(
        clips=planned_clips,
        settings=ExportPlanSettings(
            resolution=resolution,
            fps=fps,
            speed=speed,
            gap_policy=gap_policy,
        ),
        stickers=planned_stickers,
        subtitles=planned_subtitles,
        audio_tracks=planned_audio_tracks,
        filters=ExportFilterPlan(
            has_video_speed_filter=wants_speed_filter,
            has_audio_speed_filter=wants_speed_filter,
            has_subtitles=bool(planned_subtitles),
            sticker_count=len(planned_stickers),
            audio_track_count=len(planned_audio_tracks),
            needs_filter_complex=bool(
                wants_speed_filter
                or planned_stickers
                or planned_subtitles
                or planned_audio_tracks
            ),
        ),
        filter_steps=filter_steps,
        gaps=gaps,
        total_duration=total_duration,
        warnings=warnings,
    )


def _read_out_point(clip: dict, in_point: float, duration: float) -> Optional[float]:
    raw_value = clip.get("out_point", None)
    out_point = _as_float(raw_value, 0.0)

    if raw_value in (None, "", 0, 0.0):
        return in_point + duration if duration > 0.0 else None
    if out_point > in_point:
        return out_point
    return None


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_gap_policy(value: Any) -> str:
    return "reject" if str(value or "").strip().lower() == "reject" else "omit"


def _plan_gaps(
    planned_clips: list[ExportClipPlan],
    gap_policy: str,
    warnings: list[str],
) -> list[ExportGapPlan]:
    gaps = []
    cursor = 0.0
    for clip in planned_clips:
        if clip.start > cursor + 1e-6:
            duration = clip.start - cursor
            if gap_policy == "reject":
                raise ValueError(
                    f"Timeline gap rejected: start {cursor:.6f}, duration {duration:.6f}."
                )
            gaps.append(ExportGapPlan(start=cursor, duration=duration, policy=gap_policy))
            display_policy = "omitted" if gap_policy == "omit" else gap_policy
            warnings.append(
                f"Timeline gap {display_policy}: start {cursor:.6f}, duration {duration:.6f}."
            )
        cursor = max(cursor, clip.start + clip.duration)
    return gaps


def _plan_filter_steps(
    wants_speed_filter: bool,
    sticker_count: int,
    subtitle_count: int,
    audio_track_count: int,
    speed: float,
) -> list[ExportFilterStep]:
    steps = []
    if subtitle_count:
        steps.append(
            ExportFilterStep("video", "subtitles", {"count": subtitle_count})
        )
    if wants_speed_filter:
        steps.append(ExportFilterStep("video", "setpts", {"speed": speed}))
    if sticker_count:
        steps.append(ExportFilterStep("video", "overlay", {"count": sticker_count}))
    if audio_track_count:
        steps.append(ExportFilterStep("audio", "mix", {"count": audio_track_count}))
    if wants_speed_filter:
        steps.append(ExportFilterStep("audio", "atempo", {"speed": speed}))
    return steps


def _plan_stickers(stickers: list[dict], warnings: list[str]) -> list[ExportStickerPlan]:
    planned_stickers = []
    for index, sticker in enumerate(stickers):
        content = str(sticker.get("content") or "").strip()
        if not content:
            warnings.append(f"Skipping sticker {index}: missing content.")
            continue
        planned_stickers.append(
            ExportStickerPlan(
                content=content,
                x=_as_float(sticker.get("x"), 0.0),
                y=_as_float(sticker.get("y"), 0.0),
                scale=max(0.01, _as_float(sticker.get("scale"), 1.0)),
            )
        )
    return planned_stickers


def _plan_subtitles(subtitles: list[dict], warnings: list[str]) -> list[ExportSubtitlePlan]:
    planned_subtitles = []
    for index, subtitle in enumerate(subtitles):
        text_content = str(subtitle.get("text_content") or "").strip()
        if not text_content:
            warnings.append(f"Skipping subtitle {index}: empty text.")
            continue
        duration = max(0.0, _as_float(subtitle.get("duration"), 2.0))
        if duration <= 0.0:
            warnings.append(f"Skipping subtitle {index}: non-positive duration.")
            continue
        planned_subtitles.append(
            ExportSubtitlePlan(
                start_time=max(0.0, _as_float(subtitle.get("start_time"), 0.0)),
                duration=duration,
                text_content=text_content,
            )
        )
    return planned_subtitles


def _plan_audio_tracks(audio_tracks: list[dict], warnings: list[str]) -> list[ExportAudioPlan]:
    planned_audio_tracks = []
    for index, audio in enumerate(audio_tracks):
        path = str(audio.get("path") or "")
        if not path:
            warnings.append(f"Skipping audio track {index}: missing path.")
            continue
        if not os.path.exists(path):
            warnings.append(f"Skipping missing audio track path: {path}")
            continue
        planned_audio_tracks.append(
            ExportAudioPlan(
                path=path,
                start_time=max(0.0, _as_float(audio.get("start_time"), 0.0)),
                duration=max(0.0, _as_float(audio.get("duration"), 0.0)),
            )
        )
    return planned_audio_tracks


def _plan_from_dict(data: dict) -> ExportPlan:
    settings = data.get("settings") or {}
    filters = data.get("filters") or {}
    clips = [
        ExportClipPlan(
            path=str(clip.get("path") or ""),
            start=_as_float(clip.get("start"), 0.0),
            in_point=_as_float(clip.get("in_point"), 0.0),
            out_point=(
                None
                if clip.get("out_point") is None
                else _as_float(clip.get("out_point"), 0.0)
            ),
            duration=_as_float(clip.get("duration"), 0.0),
        )
        for clip in data.get("clips", [])
    ]
    return ExportPlan(
        clips=clips,
        settings=ExportPlanSettings(
            resolution=str(settings.get("resolution") or "1920x1080"),
            fps=settings.get("fps", 30),
            speed=_as_float(settings.get("speed"), 1.0),
            gap_policy=str(settings.get("gap_policy") or "omit"),
        ),
        stickers=[
            ExportStickerPlan(
                content=str(sticker.get("content") or ""),
                x=_as_float(sticker.get("x"), 0.0),
                y=_as_float(sticker.get("y"), 0.0),
                scale=_as_float(sticker.get("scale"), 1.0),
            )
            for sticker in data.get("stickers", [])
        ],
        subtitles=[
            ExportSubtitlePlan(
                start_time=_as_float(subtitle.get("start_time"), 0.0),
                duration=_as_float(subtitle.get("duration"), 0.0),
                text_content=str(subtitle.get("text_content") or ""),
            )
            for subtitle in data.get("subtitles", [])
        ],
        audio_tracks=[
            ExportAudioPlan(
                path=str(audio.get("path") or ""),
                start_time=_as_float(audio.get("start_time"), 0.0),
                duration=_as_float(audio.get("duration"), 0.0),
            )
            for audio in data.get("audio_tracks", [])
        ],
        filters=ExportFilterPlan(
            has_video_speed_filter=bool(filters.get("has_video_speed_filter")),
            has_audio_speed_filter=bool(filters.get("has_audio_speed_filter")),
            has_subtitles=bool(filters.get("has_subtitles")),
            sticker_count=int(filters.get("sticker_count") or 0),
            audio_track_count=int(filters.get("audio_track_count") or 0),
            needs_filter_complex=bool(filters.get("needs_filter_complex")),
        ),
        filter_steps=[
            ExportFilterStep(
                target=str(step.get("target") or ""),
                kind=str(step.get("kind") or ""),
                value=dict(step.get("value") or {}),
            )
            for step in data.get("filter_steps", [])
        ],
        gaps=[
            ExportGapPlan(
                start=_as_float(gap.get("start"), 0.0),
                duration=_as_float(gap.get("duration"), 0.0),
                policy=str(gap.get("policy") or "omit"),
            )
            for gap in data.get("gaps", [])
        ],
        total_duration=_as_float(data.get("total_duration"), 0.0),
        warnings=list(data.get("warnings") or []),
    )
