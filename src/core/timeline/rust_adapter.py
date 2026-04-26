from __future__ import annotations

from copy import deepcopy
from typing import Iterable, Optional

from .clip import Clip

try:
    import video_core as _video_core
except ImportError:
    _video_core = None


def is_rust_timeline_available() -> bool:
    if _video_core is None:
        return False
    try:
        return hasattr(_video_core.MagneticTrack("__probe__"), "load_clips")
    except Exception:
        return False


class NativeMagneticTimeline:
    def __init__(self, name: str):
        if _video_core is None:
            raise RuntimeError("video_core native extension is not available")
        self.name = name

    def add_clip(
        self,
        clips: list[Clip],
        clip: Clip,
        position: Optional[float] = None,
    ) -> bool:
        native_track = self._build_track(clips)
        native_clip = self._to_native_clip(clip)

        if not native_track.add_clip(native_clip, position):
            return False

        clip_map = self._clip_map([*clips, clip])
        self._sync_from_native(clips, clip_map, native_track.clips)
        return True

    def remove_clip(self, clips: list[Clip], clip_id: str) -> Optional[Clip]:
        native_track = self._build_track(clips)
        removed_native = native_track.remove_clip(clip_id)
        if removed_native is None:
            return None

        clip_map = self._clip_map(clips)
        removed_clip = clip_map.get(removed_native.id)
        if removed_clip is None:
            return None

        self._sync_from_native(clips, clip_map, native_track.clips)
        return removed_clip

    def split_clip(
        self,
        clips: list[Clip],
        clip_id: str,
        timeline_time: float,
    ) -> Optional[Clip]:
        native_track = self._build_track(clips)
        right_native = native_track.split_clip(clip_id, timeline_time)
        if right_native is None:
            return None

        source_clip = next((clip for clip in clips if clip.id == clip_id), None)
        if source_clip is None:
            return None

        right_clip = deepcopy(source_clip)
        self._sync_clip(right_clip, right_native)
        clip_map = self._clip_map(clips)
        clip_map[right_clip.id] = right_clip
        self._sync_from_native(clips, clip_map, native_track.clips)
        return right_clip

    def trim_clip(
        self,
        clips: list[Clip],
        clip_id: str,
        new_in_point: Optional[float] = None,
        new_out_point: Optional[float] = None,
    ) -> bool:
        native_track = self._build_track(clips)

        if not native_track.trim_clip(clip_id, new_in_point, new_out_point):
            return False

        self._sync_from_native(clips, self._clip_map(clips), native_track.clips)
        return True

    def _build_track(self, clips: Iterable[Clip]):
        native_track = _video_core.MagneticTrack(self.name)
        native_track.load_clips([self._to_native_clip(clip) for clip in clips])
        return native_track

    def _to_native_clip(self, clip: Clip):
        native_clip = _video_core.Clip(clip.asset_id, clip.name, float(clip.duration))
        native_clip.id = clip.id
        native_clip.start_time = float(clip.start_time)
        native_clip.in_point = float(clip.in_point)
        native_clip.out_point = float(clip.out_point)
        native_clip.track_index = int(clip.track_index)
        return native_clip

    def _sync_from_native(
        self,
        clips: list[Clip],
        clip_map: dict[str, Clip],
        native_clips,
    ) -> None:
        ordered_clips = []
        for native_clip in native_clips:
            clip = clip_map.get(native_clip.id)
            if clip is None:
                continue
            self._sync_clip(clip, native_clip)
            ordered_clips.append(clip)
        clips[:] = ordered_clips

    def _sync_clip(self, clip: Clip, native_clip) -> None:
        clip.id = native_clip.id
        clip.start_time = native_clip.start_time
        clip.in_point = native_clip.in_point
        clip.out_point = native_clip.out_point
        clip.track_index = native_clip.track_index

    def _clip_map(self, clips: Iterable[Clip]) -> dict[str, Clip]:
        return {clip.id: clip for clip in clips}
