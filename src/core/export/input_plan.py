from __future__ import annotations

from dataclasses import dataclass, field
import os
import tempfile

from ..logging_utils import get_logger
from .media_probe import get_source_resolution, source_has_audio
from .planner import ExportPlan, ExportStickerPlan
from .subtitle_asset import create_ass_subtitle_file

logger = get_logger(__name__)


@dataclass(frozen=True)
class InputAssetPlan:
    concat_path: str
    additional_input_args: list[str] = field(default_factory=list)
    temp_files: list[str] = field(default_factory=list)
    video_filters: list[str] = field(default_factory=list)
    sticker_overlays: list[tuple[int, int]] = field(default_factory=list)
    sticker_input_count: int = 0
    audio_input_count: int = 0
    first_video_path: str = ""
    render_size: tuple[int, int] = (1920, 1080)
    has_source_audio: bool = False


def build_input_asset_plan(export_plan: ExportPlan, ffmpeg_path: str) -> InputAssetPlan:
    concat_path = _create_concat_file(export_plan)
    first_video_path = _find_first_existing_video(export_plan)
    render_size = _resolve_render_size(export_plan, first_video_path)

    sticker_inputs, sticker_overlays, sticker_temp_files = _create_sticker_inputs(
        export_plan,
        render_size,
    )
    video_filters, subtitle_temp_files = _create_subtitle_filters(export_plan, render_size)
    audio_inputs = [audio.path for audio in export_plan.audio_tracks]

    additional_input_args = []
    for sticker_path in sticker_inputs:
        additional_input_args.extend(["-i", sticker_path])
    for audio_path in audio_inputs:
        additional_input_args.extend(["-i", audio_path])

    if audio_inputs:
        logger.info("Audio mix inputs: %s track(s)", len(audio_inputs))

    return InputAssetPlan(
        concat_path=concat_path,
        additional_input_args=additional_input_args,
        temp_files=[*sticker_temp_files, *subtitle_temp_files],
        video_filters=video_filters,
        sticker_overlays=sticker_overlays,
        sticker_input_count=len(sticker_inputs),
        audio_input_count=len(audio_inputs),
        first_video_path=first_video_path,
        render_size=render_size,
        has_source_audio=source_has_audio(first_video_path, ffmpeg_path),
    )


def _create_concat_file(export_plan: ExportPlan) -> str:
    concat_fd, concat_path = tempfile.mkstemp(suffix=".txt", prefix="concat_", text=True)
    with os.fdopen(concat_fd, "w", encoding="utf-8") as concat_file:
        for clip in export_plan.clips:
            escaped_path = clip.path.replace("'", "'\\''")
            concat_file.write(f"file '{escaped_path}'\n")
            if clip.in_point > 0.0:
                concat_file.write(f"inpoint {clip.in_point:.6f}\n")
            if clip.out_point is not None and clip.out_point > clip.in_point:
                concat_file.write(f"outpoint {clip.out_point:.6f}\n")
    return concat_path


def _find_first_existing_video(export_plan: ExportPlan) -> str:
    for clip in export_plan.clips:
        if clip.path and os.path.exists(clip.path):
            return clip.path
    return ""


def _resolve_render_size(export_plan: ExportPlan, first_video_path: str) -> tuple[int, int]:
    resolution = export_plan.settings.resolution
    if isinstance(resolution, str) and resolution.lower() == "original":
        detected_size = get_source_resolution(first_video_path)
        if detected_size:
            return detected_size
        return (1920, 1080)

    try:
        width, height = map(int, str(resolution).split("x"))
    except Exception:
        return (1920, 1080)

    if width > 0 and height > 0:
        return (width, height)
    return (1920, 1080)


def _create_sticker_inputs(
    export_plan: ExportPlan,
    render_size: tuple[int, int],
) -> tuple[list[str], list[tuple[int, int]], list[str]]:
    if not export_plan.stickers:
        return [], [], []

    try:
        from PIL import Image, ImageDraw, ImageFont
        import platform
    except ImportError as exc:
        logger.warning("Pillow not available for sticker export: %s", exc)
        return [], [], []

    sticker_inputs = []
    sticker_overlays = []
    temp_files = []

    try:
        for index, sticker in enumerate(export_plan.stickers):
            sticker_asset = _create_sticker_asset(
                sticker,
                index,
                render_size,
                Image,
                ImageDraw,
                ImageFont,
                platform.system(),
            )
            if not sticker_asset:
                continue
            sticker_path, overlay_position = sticker_asset
            sticker_inputs.append(sticker_path)
            sticker_overlays.append(overlay_position)
            temp_files.append(sticker_path)
    except Exception as exc:
        logger.warning("Error creating sticker images: %s", exc)

    return sticker_inputs, sticker_overlays, temp_files


def _create_sticker_asset(
    sticker: ExportStickerPlan,
    index: int,
    render_size: tuple[int, int],
    image_module,
    image_draw_module,
    image_font_module,
    platform_name: str,
) -> tuple[str, tuple[int, int]] | None:
    if not sticker.content:
        return None

    image_size = int(200 * sticker.scale)
    image = image_module.new("RGBA", (image_size, image_size), (0, 0, 0, 0))
    draw = image_draw_module.Draw(image)
    font_size = int(100 * sticker.scale)
    font = _load_sticker_font(image_font_module, platform_name, font_size)
    draw.text((image_size // 2, image_size // 2), sticker.content, font=font, anchor="mm")

    sticker_fd, sticker_path = tempfile.mkstemp(
        suffix=f"_sticker_{index}.png",
        prefix="export_",
    )
    os.close(sticker_fd)
    image.save(sticker_path, "PNG")

    render_width, render_height = render_size
    absolute_x = int(render_width / 2 + sticker.x - image_size / 2)
    absolute_y = int(render_height / 2 + sticker.y - image_size / 2)
    return sticker_path, (absolute_x, absolute_y)


def _load_sticker_font(image_font_module, platform_name: str, font_size: int):
    try:
        if platform_name == "Darwin":
            return image_font_module.truetype(
                "/System/Library/Fonts/Apple Color Emoji.ttc",
                font_size,
            )
        return image_font_module.truetype(
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
            font_size,
        )
    except Exception:
        return image_font_module.load_default()


def _create_subtitle_filters(
    export_plan: ExportPlan,
    render_size: tuple[int, int],
) -> tuple[list[str], list[str]]:
    subtitle_file = create_ass_subtitle_file(
        export_plan.subtitles,
        render_size[0],
        render_size[1],
    )
    if not subtitle_file:
        return [], []

    escaped_path = (
        subtitle_file.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    )
    logger.info("Created subtitle file: %s", subtitle_file)
    return [f"subtitles='{escaped_path}'"], [subtitle_file]
