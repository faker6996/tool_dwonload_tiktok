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

        # Create sticker images and build overlay filter
        sticker_inputs = []  # Additional input files for stickers
        overlay_filter = ""
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
                    sticker_path = tempfile.mktemp(suffix=f"_sticker_{idx}.png", prefix="export_")
                    img.save(sticker_path, "PNG")
                    temp_sticker_files.append(sticker_path)
                    
                    # Calculate absolute position
                    abs_x = int(res_w / 2 + x - img_size / 2)
                    abs_y = int(res_h / 2 + y - img_size / 2)
                    
                    # Add input and overlay filter
                    sticker_inputs.extend(["-i", sticker_path])
                    
                    if idx == 0:
                        overlay_filter = f"[0:v][1:v]overlay={abs_x}:{abs_y}"
                    else:
                        overlay_filter += f"[tmp{idx-1}];[tmp{idx-1}][{idx+1}:v]overlay={abs_x}:{abs_y}"
                    
                    if idx < len(stickers_list) - 1:
                        overlay_filter += f"[tmp{idx}]"
                        
            except ImportError as e:
                print(f"Pillow not available for sticker export: {e}")
            except Exception as e:
                print(f"Error creating sticker images: {e}")
        
        # Store temp files for cleanup
        self._temp_sticker_files = temp_sticker_files

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_path,
        ]
        
        # Add sticker image inputs
        cmd.extend(sticker_inputs)
        
        cmd.extend([
            "-r",
            str(fps),
            "-s",
            resolution,
        ])
        
        # Add overlay filter if we have stickers
        if overlay_filter:
            cmd.extend(["-filter_complex", overlay_filter])
        
        cmd.extend([
            "-c:v",
            "libx264",
            "-c:a",
            "aac",  # Re-encode audio 
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",  # Move moov atom to beginning for streaming
            output_path,
        ])
        
        print(f"FFmpeg command: {' '.join(cmd)}")

        return cmd, concat_path

# Global instance
render_engine = RenderEngine()
