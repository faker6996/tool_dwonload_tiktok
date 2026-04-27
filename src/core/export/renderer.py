import subprocess
import os
import sys
from typing import List, Dict, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal
from ..logging_utils import get_logger
from ..profiling import profile_scope
from .command_plan import build_output_command_plan
from .filter_graph import build_filter_graph
from .input_plan import build_input_asset_plan
from .planner import build_export_plan

logger = get_logger(__name__)


def get_ffmpeg_path() -> str:
    """Get path to FFmpeg binary - bundled or system."""
    # Check for bundled FFmpeg first
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    # Check bundled locations
    bundled_paths = [
        os.path.join(base_path, 'bin', 'ffmpeg'),
        os.path.join(base_path, 'bin', 'ffmpeg.exe'),
        os.path.join(base_path, 'ffmpeg'),
        os.path.join(base_path, 'ffmpeg.exe'),
    ]
    
    for path in bundled_paths:
        if os.path.exists(path):
            logger.info("Using bundled FFmpeg: %s", path)
            return path
    
    # Fall back to system FFmpeg
    logger.info("Using system FFmpeg")
    return "ffmpeg"


class RenderEngine(QObject):
    progress_updated = pyqtSignal(int) # 0-100
    render_finished = pyqtSignal(bool, str) # Success, Message

    def __init__(self):
        super().__init__()
        self.output_path = ""
        self.ffmpeg_path = get_ffmpeg_path()
        self.settings = {
            "resolution": "1920x1080",
            "fps": 30,
            "format": "mp4",
            "quality": "High" # High, Medium, Low
        }


    def render_timeline(self, timeline_clips: List[Dict], output_path: str, settings: Dict, stickers: List[Dict] = None, subtitles: List[Dict] = None, audio_tracks: List[Dict] = None):
        """
        Render the timeline to a video file.
        timeline_clips: List of clip data (path, start, duration, etc.)
        stickers: List of sticker data to overlay (content, x, y, scale, rotation)
        subtitles: List of subtitle clips (start_time, duration, text_content)
        audio_tracks: List of audio clips to mix (path, start_time, duration)
        """
        self.output_path = output_path
        # Playback rate is a preview-only UI concern; never bake it into export settings.
        safe_settings = dict(settings or {})
        safe_settings.pop("playback_rate", None)
        safe_settings.pop("preview_playback_rate", None)
        self.settings.update(safe_settings)
        self.stickers = stickers or []
        self.subtitles = subtitles or []
        self.audio_tracks = audio_tracks or []
        
        logger.info("Starting render to %s with settings %s", output_path, self.settings)
        if self.stickers:
            logger.info("Rendering %s stickers", len(self.stickers))
        if self.subtitles:
            logger.info("Burning %s subtitles into video", len(self.subtitles))
        if self.audio_tracks:
            logger.info("Mixing %s audio tracks (TTS/voiceover)", len(self.audio_tracks))

        if not timeline_clips:
            self.render_finished.emit(False, "No clips to render.")
            return

        try:
            with profile_scope(
                "export.render_prepare",
                clip_count=len(timeline_clips),
                sticker_count=len(self.stickers),
                subtitle_count=len(self.subtitles),
                audio_count=len(self.audio_tracks),
            ):
                cmd, concat_file, temp_files = self._build_ffmpeg_command(timeline_clips, output_path)
        except Exception as e:
            self.render_finished.emit(False, f"Failed to build FFmpeg command: {e}")
            return

        import threading
        import time

        def run_render():
            try:
                # Start ffmpeg process
                with profile_scope(
                    "export.ffmpeg_render",
                    clip_count=len(timeline_clips),
                    has_filters="-filter_complex" in cmd,
                ):
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )

                    # Simple progress simulation while ffmpeg runs
                    progress = 0
                    while True:
                        if process.poll() is not None:
                            break
                        progress = min(progress + 2, 95)
                        self.progress_updated.emit(progress)
                        time.sleep(0.1)

                    stdout, stderr = process.communicate()
                if process.returncode == 0 and os.path.exists(output_path):
                    self.progress_updated.emit(100)
                    self.render_finished.emit(True, "Render completed successfully!")
                else:
                    msg = "FFmpeg failed."
                    if stderr:
                        msg = f"FFmpeg error: {stderr.splitlines()[-1]}"
                    self.render_finished.emit(False, msg)
            finally:
                try:
                    if concat_file and os.path.exists(concat_file):
                        os.remove(concat_file)
                except Exception:
                    pass
                for temp_path in temp_files:
                    try:
                        if temp_path and os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception:
                        pass

        threading.Thread(target=run_render, daemon=True).start()

    def _build_ffmpeg_command(self, clips: List[Dict], output_path: str) -> Tuple[List[str], Optional[str], List[str]]:
        """
        Build a simple FFmpeg concat command from a list of clips.
        Each clip dict must contain: path.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        export_plan = build_export_plan(
            clips,
            self.settings,
            getattr(self, "stickers", []),
            getattr(self, "subtitles", []),
            getattr(self, "audio_tracks", []),
        )
        for warning in export_plan.warnings:
            logger.warning(warning)

        input_plan = build_input_asset_plan(export_plan, self.ffmpeg_path)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            input_plan.concat_path,
        ]

        cmd.extend(input_plan.additional_input_args)

        output_command_plan = build_output_command_plan(export_plan)
        cmd.extend(output_command_plan.fps_args)
        cmd.extend(output_command_plan.size_args)
        
        filter_graph = build_filter_graph(
            export_plan=export_plan,
            video_filters=input_plan.video_filters,
            sticker_overlays=input_plan.sticker_overlays,
            sticker_input_count=input_plan.sticker_input_count,
            audio_input_count=input_plan.audio_input_count,
            has_source_audio=input_plan.has_source_audio,
        )
        if filter_graph.needs_filter_complex:
            cmd.extend(["-filter_complex", filter_graph.filter_complex])
            cmd.extend(filter_graph.map_args)
            cmd.extend(output_command_plan.audio_codec_args)
        else:
            cmd.extend(["-map", "0:v", "-map", "0:a?"])
            cmd.extend(output_command_plan.audio_codec_args)
        
        cmd.extend(output_command_plan.video_codec_args)
        cmd.append(output_path)
        
        logger.debug("FFmpeg command: %s", " ".join(cmd))

        return cmd, input_plan.concat_path, input_plan.temp_files

# Global instance
render_engine = RenderEngine()
