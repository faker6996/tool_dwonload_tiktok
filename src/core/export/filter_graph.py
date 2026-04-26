from __future__ import annotations

from dataclasses import dataclass

from .planner import ExportPlan


@dataclass(frozen=True)
class FilterGraphBuild:
    filter_complex: str
    map_args: list[str]
    needs_filter_complex: bool


def build_filter_graph(
    export_plan: ExportPlan,
    video_filters: list[str],
    sticker_overlays: list[tuple[int, int]],
    sticker_input_count: int,
    audio_input_count: int,
    has_source_audio: bool,
) -> FilterGraphBuild:
    planned_video_filters = list(video_filters)
    if export_plan.has_filter_step("video", "setpts"):
        planned_video_filters.append(f"setpts=PTS/{export_plan.settings.speed:g}")

    filter_parts = []
    video_map_label = "0:v"
    video_graph_label = "[0:v]"

    if planned_video_filters:
        filter_parts.append(f"[0:v]{','.join(planned_video_filters)}[v0]")
        video_graph_label = "[v0]"
        video_map_label = "[v0]"

    if sticker_input_count > 0:
        previous_label = video_graph_label
        for index, (abs_x, abs_y) in enumerate(sticker_overlays):
            sticker_label = f"[{1 + index}:v]"
            output_label = f"[v{index + 1}]"
            filter_parts.append(
                f"{previous_label}{sticker_label}overlay={abs_x}:{abs_y}{output_label}"
            )
            previous_label = output_label
        video_map_label = previous_label

    audio_output_label = _build_audio_filter_parts(
        filter_parts,
        export_plan,
        sticker_input_count,
        audio_input_count,
        has_source_audio,
    )

    needs_filter_complex = bool(filter_parts)
    map_args = ["-map", video_map_label]
    if audio_output_label:
        map_args.extend(["-map", audio_output_label])
    else:
        map_args.extend(["-map", "0:a?"])

    return FilterGraphBuild(
        filter_complex=";".join(filter_parts),
        map_args=map_args,
        needs_filter_complex=needs_filter_complex,
    )


def _build_audio_filter_parts(
    filter_parts: list[str],
    export_plan: ExportPlan,
    sticker_input_count: int,
    audio_input_count: int,
    has_source_audio: bool,
) -> str:
    wants_audio_speed = export_plan.has_filter_step("audio", "atempo")
    audio_base_label = ""

    if audio_input_count > 0:
        audio_base_index = 1 + sticker_input_count
        mix_labels = []
        if has_source_audio:
            filter_parts.append("[0:a]volume=0.5[orig]")
            mix_labels.append("[orig]")
        mix_labels.extend(f"[{audio_base_index + index}:a]" for index in range(audio_input_count))

        if len(mix_labels) == 1:
            filter_parts.append(f"{mix_labels[0]}anull[aout]")
            audio_base_label = "[aout]"
        else:
            filter_parts.append(
                f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=longest[aout]"
            )
            audio_base_label = "[aout]"
    elif wants_audio_speed and has_source_audio:
        audio_base_label = "[0:a]"

    if wants_audio_speed and audio_base_label:
        filter_parts.append(f"{audio_base_label}atempo={export_plan.settings.speed:g}[aout_speed]")
        return "[aout_speed]"

    return audio_base_label
