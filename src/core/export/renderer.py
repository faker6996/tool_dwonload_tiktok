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

    def render_timeline(self, timeline_clips: List[Dict], output_path: str, settings: Dict):
        """
        Render the timeline to a video file.
        timeline_clips: List of clip data (path, start, duration, etc.)
        """
        self.output_path = output_path
        self.settings.update(settings)
        
        print(f"Starting render to {output_path} with settings {self.settings}")

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
                # FFmpeg concat demuxer format
                f.write(f"file '{path.replace(\"'\", \"'\\\\''\")}'\n")

        resolution = self.settings.get("resolution", "1920x1080")
        fps = int(self.settings.get("fps", 30))

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
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]

        return cmd, concat_path

# Global instance
render_engine = RenderEngine()
