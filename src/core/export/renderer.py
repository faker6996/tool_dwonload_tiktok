import subprocess
import os
import tempfile
from typing import List, Dict, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal

class RenderEngine(QObject):
    progress_updated = pyqtSignal(int) # 0-100
    render_finished = pyqtSignal(bool, str) # Success, Message

    def __init__(self):
        super().__init__()
        self.output_path = ""
        self.settings = {
            "resolution": "1920x1080",
            "fps": 30,
            "format": "mp4",
            "quality": "High" # High, Medium, Low
        }

    def render_timeline(self, timeline_clips: List[Dict], output_path: str, settings: Dict, stickers: List[Dict] = None):
        """
        Render the timeline to a video file.
        timeline_clips: List of clip data (path, start, duration, etc.)
        stickers: List of sticker data to overlay (content, x, y, scale, rotation)
        """
        self.output_path = output_path
        self.settings.update(settings)
        self.stickers = stickers or []
        
        print(f"Starting render to {output_path} with settings {self.settings}")
        if self.stickers:
            print(f"Rendering {len(self.stickers)} stickers")

        if not timeline_clips:
            self.render_finished.emit(False, "No clips to render.")
            return

        try:
            cmd, concat_file = self._build_ffmpeg_command(timeline_clips, output_path)
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

        threading.Thread(target=run_render, daemon=True).start()

    def _build_ffmpeg_command(self, clips: List[Dict], output_path: str) -> Tuple[List[str], Optional[str]]:
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
        fps = int(self.settings.get("fps", 30))
        
        # Parse resolution for sticker positioning
        try:
            res_w, res_h = map(int, resolution.split("x"))
        except:
            res_w, res_h = 1920, 1080

        # Build video filter for stickers
        vf_parts = []
        
        # Add sticker overlays using drawtext filter
        for sticker in getattr(self, "stickers", []):
            content = sticker.get("content", "")
            if not content:
                continue
            
            # Position relative to center - convert to absolute coords
            x = sticker.get("x", 0)
            y = sticker.get("y", 0)
            scale = sticker.get("scale", 1.0)
            
            # Convert center-relative to absolute position
            abs_x = int(res_w / 2 + x)
            abs_y = int(res_h / 2 + y)
            
            # Calculate font size based on scale (base 72pt)
            fontsize = int(72 * scale)
            
            # Escape special characters for FFmpeg
            escaped_content = content.replace("'", "'\\''").replace(":", "\\:")
            
            # drawtext filter - use system emoji font
            drawtext = f"drawtext=text='{escaped_content}':fontsize={fontsize}:x={abs_x}:y={abs_y}:fontcolor=white"
            vf_parts.append(drawtext)

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_path,
            "-r",
            str(fps),
            "-s",
            resolution,
        ]
        
        # Add video filter if we have stickers
        if vf_parts:
            vf_string = ",".join(vf_parts)
            cmd.extend(["-vf", vf_string])
        
        cmd.extend([
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            output_path,
        ])

        return cmd, concat_path

# Global instance
render_engine = RenderEngine()
