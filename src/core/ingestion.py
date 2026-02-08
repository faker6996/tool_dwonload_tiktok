import subprocess
import json
import os
import hashlib
from typing import Dict, Optional
from .logging_utils import get_logger

logger = get_logger(__name__)

class MediaIngestion:
    def __init__(self):
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".video_downloader", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def probe_file(self, file_path: str) -> Optional[Dict]:
        """
        Run ffprobe to extract metadata from the file.
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return self._parse_metadata(data, file_path)
        except subprocess.CalledProcessError as e:
            logger.warning("Error probing file %s: %s", file_path, e)
            return None
        except json.JSONDecodeError as e:
            logger.warning("Error parsing ffprobe output for %s: %s", file_path, e)
            return None

    def _parse_metadata(self, data: Dict, file_path: str) -> Dict:
        """
        Parse raw ffprobe JSON into our internal Asset Schema.
        """
        format_info = data.get("format", {})
        streams = data.get("streams", [])
        
        video_stream = next((s for s in streams if s["codec_type"] == "video"), {})
        audio_stream = next((s for s in streams if s["codec_type"] == "audio"), {})
        
        duration = float(format_info.get("duration", 0))
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        frame_rate_str = video_stream.get("r_frame_rate", "0/0")
        
        # Calculate FPS from fraction string (e.g., "30000/1001")
        try:
            num, den = map(int, frame_rate_str.split('/'))
            fps = num / den if den != 0 else 0
        except ValueError:
            fps = 0.0

        codec = video_stream.get("codec_name", "unknown")
        
        # Generate Thumbnail
        thumbnail_path = self._generate_thumbnail(file_path)
        
        # Generate Waveform (if audio exists)
        waveform_path = ""
        if audio_stream:
            waveform_path = self.generate_waveform(file_path)

        # Generate Proxy (Optional, can be triggered later)
        # proxy_path = self.generate_proxy(file_path)
        
        return {
            "id": str(hashlib.md5(file_path.encode()).hexdigest()), # Simple ID generation
            "name": os.path.basename(file_path),
            "target_url": file_path,
            "metadata": {
                "width": width,
                "height": height,
                "frameRate": fps,
                "duration": duration,
                "codec": codec,
                "thumbnailPath": thumbnail_path,
                "waveformPath": waveform_path
            },
            "status": "ready"
        }

    def _generate_thumbnail(self, file_path: str) -> str:
        """
        Generate a thumbnail using ffmpeg with fast seeking.
        """
        file_hash = hashlib.md5(f"{file_path}_{os.path.getmtime(file_path)}".encode()).hexdigest()
        thumbnail_path = os.path.join(self.cache_dir, f"thumb_{file_hash}.jpg")
        
        if os.path.exists(thumbnail_path):
            return thumbnail_path
            
        cmd = [
            "ffmpeg",
            "-ss", "00:00:05.000", # Fast seek to 5s
            "-i", file_path,
            "-frames:v", "1",
            "-vf", "scale=320:-1", # Downscale
            "-q:v", "2", # High quality JPEG
            "-y", # Overwrite
            thumbnail_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return thumbnail_path
        except subprocess.CalledProcessError as e:
            logger.warning("Error generating thumbnail for %s: %s", file_path, e)
            return ""

    def generate_waveform(self, file_path: str) -> str:
        """
        Generate a waveform image using ffmpeg.
        Returns path to the waveform PNG.
        """
        file_hash = hashlib.md5(f"{file_path}_{os.path.getmtime(file_path)}".encode()).hexdigest()
        waveform_path = os.path.join(self.cache_dir, f"wave_{file_hash}.png")
        
        if os.path.exists(waveform_path):
            return waveform_path
            
        # Generate waveform using showwavespic filter
        cmd = [
            "ffmpeg",
            "-i", file_path,
            "-filter_complex", "showwavespic=s=640x120:colors=cyan|blue",
            "-frames:v", "1",
            "-y",
            waveform_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return waveform_path
        except subprocess.CalledProcessError as e:
            logger.warning("Error generating waveform for %s: %s", file_path, e)
            return ""

    def generate_proxy(self, file_path: str) -> str:
        """
        Generate a low-res proxy for the video.
        """
        cache_dir = os.path.join(os.path.expanduser("~"), ".video_downloader_cache", "proxies")
        os.makedirs(cache_dir, exist_ok=True)
        
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        output_path = os.path.join(cache_dir, f"{file_hash}_proxy.mp4")
        
        if os.path.exists(output_path):
            return output_path
            
        # Simulate Proxy Generation (FFmpeg downscale)
        # cmd = f'ffmpeg -i "{file_path}" -vf scale=640:-1 -c:v libx264 -crf 28 -preset ultrafast "{output_path}"'
        # subprocess.run(cmd, shell=True)
        
        # For MVP, just create a dummy small file
        with open(output_path, 'w') as f:
            f.write("Proxy Data")
            
        return output_path
