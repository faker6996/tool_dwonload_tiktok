import subprocess
import os
import sys
import tempfile
from typing import List, Dict, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal


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
            print(f"Using bundled FFmpeg: {path}")
            return path
    
    # Fall back to system FFmpeg
    print("Using system FFmpeg")
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
        
        print(f"Starting render to {output_path} with settings {self.settings}")
        if self.stickers:
            print(f"Rendering {len(self.stickers)} stickers")
        if self.subtitles:
            print(f"Burning {len(self.subtitles)} subtitles into video")
        if self.audio_tracks:
            print(f"Mixing {len(self.audio_tracks)} audio tracks (TTS/voiceover)")

        if not timeline_clips:
            self.render_finished.emit(False, "No clips to render.")
            return

        try:
            cmd, concat_file, temp_files = self._build_ffmpeg_command(timeline_clips, output_path)
        except Exception as e:
            self.render_finished.emit(False, f"Failed to build FFmpeg command: {e}")
            return

        import threading
        import time

        def run_render():
            try:
                # Start ffmpeg process
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

        # Create concat list file
        concat_fd, concat_path = tempfile.mkstemp(suffix=".txt", prefix="concat_", text=True)
        with os.fdopen(concat_fd, "w") as f:
            for clip in clips:
                path = clip.get("path")
                if not path:
                    continue
                # FFmpeg concat demuxer format - escape single quotes
                escaped_path = path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")

        resolution = self.settings.get("resolution", "1920x1080")
        fps_setting = self.settings.get("fps", 30)
        speed_setting = self.settings.get("speed", self.settings.get("export_speed", 1.0))
        try:
            speed = float(speed_setting)
        except Exception:
            speed = 1.0
        if speed <= 0:
            speed = 1.0

        def get_source_resolution(video_path: str) -> Optional[Tuple[int, int]]:
            try:
                import cv2  # type: ignore
            except Exception:
                return None

            cap = cv2.VideoCapture(video_path)
            try:
                if not cap.isOpened():
                    return None
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
                if width > 0 and height > 0:
                    return width, height
                return None
            finally:
                cap.release()

        def source_has_audio(video_path: str) -> bool:
            if not video_path:
                return False
            try:
                probe = subprocess.run(
                    [self.ffmpeg_path, "-hide_banner", "-i", video_path],
                    capture_output=True,
                    text=True,
                )
                stderr = (probe.stderr or "") + (probe.stdout or "")
                return "Audio:" in stderr
            except Exception:
                return False

        # Parse resolution for sticker/subtitle positioning. If "original", detect from first clip.
        res_w, res_h = 1920, 1080
        first_path = ""
        for clip in clips:
            p = clip.get("path")
            if p:
                first_path = p
                break

        if isinstance(resolution, str) and resolution.lower() == "original":
            detected = get_source_resolution(first_path) if first_path else None
            if detected:
                res_w, res_h = detected
        else:
            try:
                res_w, res_h = map(int, str(resolution).split("x"))
            except Exception:
                res_w, res_h = 1920, 1080

        # Create sticker images and prepare overlay data
        sticker_inputs = []  # Additional input files for stickers
        sticker_overlays = []  # (abs_x, abs_y) per sticker input
        temp_sticker_files = []
        
        stickers_list = getattr(self, "stickers", [])
        if stickers_list:
            try:
                from PIL import Image, ImageDraw, ImageFont
                import platform
                
                for idx, sticker in enumerate(stickers_list):
                    content = sticker.get("content", "")
                    if not content:
                        continue
                    
                    # Position relative to center - convert to absolute coords
                    x = sticker.get("x", 0)
                    y = sticker.get("y", 0)
                    scale = sticker.get("scale", 1.0)
                    
                    # Create PNG image with emoji
                    img_size = int(200 * scale)
                    img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(img)
                    
                    # Try to load emoji font
                    font_size = int(100 * scale)
                    try:
                        if platform.system() == "Darwin":  # macOS
                            font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", font_size)
                        else:
                            font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                    
                    # Draw emoji centered
                    draw.text((img_size//2, img_size//2), content, font=font, anchor="mm")
                    
                    # Save temporary PNG
                    sticker_fd, sticker_path = tempfile.mkstemp(suffix=f"_sticker_{idx}.png", prefix="export_")
                    os.close(sticker_fd)
                    img.save(sticker_path, "PNG")
                    temp_sticker_files.append(sticker_path)
                    
                    # Calculate absolute position
                    abs_x = int(res_w / 2 + x - img_size / 2)
                    abs_y = int(res_h / 2 + y - img_size / 2)
                    
                    # Add input and overlay data
                    sticker_inputs.append(sticker_path)
                    sticker_overlays.append((abs_x, abs_y))
                        
            except ImportError as e:
                print(f"Pillow not available for sticker export: {e}")
            except Exception as e:
                print(f"Error creating sticker images: {e}")
        
        # Store temp files for cleanup
        temp_files = list(temp_sticker_files)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_path,
        ]

        # Add sticker image inputs
        for sticker_path in sticker_inputs:
            cmd.extend(["-i", sticker_path])
        
        # Build video filter chain
        video_filters = []
        
        # Add subtitles filter if we have subtitles
        subtitles_list = getattr(self, "subtitles", [])
        subtitle_file = None
        if subtitles_list:
            try:
                # Create ASS subtitle file
                subtitle_file = self._create_ass_subtitle_file(subtitles_list, res_w, res_h)
                if subtitle_file:
                    # Escape path for FFmpeg filter
                    escaped_path = subtitle_file.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
                    video_filters.append(f"subtitles='{escaped_path}'")
                    print(f"Created subtitle file: {subtitle_file}")
            except Exception as e:
                print(f"Error creating subtitles: {e}")
        if subtitle_file:
            temp_files.append(subtitle_file)

        # Export speed (video) - apply after subtitle burn-in so subtitle timing scales with speed.
        if abs(speed - 1.0) > 1e-6:
            video_filters.append(f"setpts=PTS/{speed:g}")
        
        # Build audio mixing if we have TTS/audio tracks
        audio_tracks_list = getattr(self, "audio_tracks", [])
        audio_inputs = []
        audio_input_files = []
        
        if audio_tracks_list:
            # Add each audio file as input
            for audio in audio_tracks_list:
                audio_path = audio.get("path", "")
                if audio_path and os.path.exists(audio_path):
                    audio_input_files.append(audio_path)
                    audio_inputs.extend(["-i", audio_path])
            
            if audio_input_files:
                print(f"Audio mix inputs: {len(audio_input_files)} track(s)")

        # Add audio inputs after sticker inputs
        cmd.extend(audio_inputs)

        if not (isinstance(fps_setting, str) and fps_setting.lower() == "original"):
            try:
                fps_value = float(fps_setting)
                if fps_value > 0:
                    cmd.extend(["-r", str(fps_value)])
            except Exception:
                cmd.extend(["-r", "30"])
        if not (isinstance(resolution, str) and resolution.lower() == "original"):
            cmd.extend(["-s", str(resolution)])
        
        # Build filter_complex if needed
        needs_filter_complex = bool(video_filters or sticker_inputs or audio_input_files)
        if needs_filter_complex:
            filter_parts = []

            # Video chain
            video_map_label = "0:v"
            video_graph_label = "[0:v]"
            if video_filters:
                filter_parts.append(f"[0:v]{','.join(video_filters)}[v0]")
                video_graph_label = "[v0]"
                video_map_label = "[v0]"

            if sticker_inputs:
                base_index = 1
                prev_label = video_graph_label
                for i, (abs_x, abs_y) in enumerate(sticker_overlays):
                    sticker_label = f"[{base_index + i}:v]"
                    out_label = f"[v{i + 1}]"
                    filter_parts.append(f"{prev_label}{sticker_label}overlay={abs_x}:{abs_y}{out_label}")
                    prev_label = out_label
                video_graph_label = prev_label
                video_map_label = prev_label

            # Audio chain
            audio_output_label = ""
            has_source_audio = source_has_audio(first_path)
            wants_audio_speed = abs(speed - 1.0) > 1e-6
            audio_base_label = ""

            if audio_input_files:
                audio_base_index = 1 + len(sticker_inputs)
                mix_labels = []
                if has_source_audio:
                    filter_parts.append("[0:a]volume=0.5[orig]")
                    mix_labels.append("[orig]")
                mix_labels.extend(
                    f"[{audio_base_index + i}:a]" for i in range(len(audio_input_files))
                )

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
                filter_parts.append(f"{audio_base_label}atempo={speed:g}[aout_speed]")
                audio_output_label = "[aout_speed]"
            else:
                audio_output_label = audio_base_label

            cmd.extend(["-filter_complex", ";".join(filter_parts)])

            # Map outputs
            cmd.extend(["-map", video_map_label])
            if audio_output_label:
                cmd.extend(["-map", audio_output_label])
            else:
                cmd.extend(["-map", "0:a?"])

            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-map", "0:v", "-map", "0:a?"])
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        
        cmd.extend([
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
            output_path,
        ])
        
        print(f"FFmpeg command: {' '.join(cmd)}")

        return cmd, concat_path, temp_files

    def _create_ass_subtitle_file(self, subtitles: List[Dict], video_width: int, video_height: int) -> Optional[str]:
        """
        Create an ASS subtitle file from subtitle clips.
        Returns path to the created file.
        """
        if not subtitles:
            return None
        
        # ASS header with styling (matching player preview style)
        # Font size 56, white text, black outline (3px), centered at bottom
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
        for sub in subtitles:
            start_time = sub.get("start_time", 0)
            duration = sub.get("duration", 2)
            text = sub.get("text_content", "").strip()
            
            if not text:
                continue
            
            end_time = start_time + duration
            
            # Convert to ASS time format: H:MM:SS.CC
            start_str = self._format_ass_time(start_time)
            end_str = self._format_ass_time(end_time)
            
            # Escape special characters in ASS
            text = text.replace("\\", "/").replace("{", "\\{").replace("}", "\\}")
            text = text.replace("\n", "\\N")
            
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")
        
        if not events:
            return None
        
        # Write ASS file
        ass_fd, ass_path = tempfile.mkstemp(suffix=".ass", prefix="subtitles_", text=True)
        with os.fdopen(ass_fd, "w", encoding="utf-8") as f:
            f.write(ass_header)
            f.write("\n".join(events))
        
        return ass_path
    
    def _format_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format H:MM:SS.CC"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds * 100) % 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

# Global instance
render_engine = RenderEngine()
