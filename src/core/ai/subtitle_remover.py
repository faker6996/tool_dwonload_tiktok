"""
Subtitle Removal Service using OpenCV inpainting.
Detects and removes hardcoded subtitles from video frames.
"""
import cv2
import numpy as np
from typing import Tuple, Optional
import os


class SubtitleRemoverService:
    """Service for detecting and removing hardcoded subtitles from videos."""
    
    def __init__(self):
        self.subtitle_region = None  # (x, y, w, h) or None for auto-detect
        self.inpaint_radius = 3
        self.detection_threshold = 200  # For text detection
    
    def remove_subtitles_ffmpeg(self, input_path: str, output_path: str,
                                  bottom_percent: float = 0.15,
                                  method: str = "crop",
                                  progress_callback=None) -> bool:
        """
        Fast subtitle removal using FFmpeg.
        
        Args:
            input_path: Input video path
            output_path: Output video path  
            bottom_percent: Percentage of video height to remove (default 15%)
            method: "crop" (remove bottom), "blur" (blur bottom), "black" (black out)
            progress_callback: Optional callback(percent)
        
        Returns:
            True if successful
        """
        import subprocess
        
        # Get video dimensions first
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            input_path
        ]
        
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            width, height = map(int, result.stdout.strip().split('x'))
            print(f"📐 Video: {width}x{height}")
        except:
            width, height = 1920, 1080  # Default
        
        # Calculate crop/blur region
        crop_height = int(height * (1 - bottom_percent))
        blur_y = int(height * (1 - bottom_percent))
        blur_h = int(height * bottom_percent)
        
        if method == "crop":
            # Crop video to remove bottom portion
            filter_complex = f"crop=w={width}:h={crop_height}:x=0:y=0"
        elif method == "blur":
            # Blur bottom portion
            filter_complex = f"[0:v]split[main][blur];[blur]crop={width}:{blur_h}:0:{blur_y},boxblur=20:20[blurred];[main][blurred]overlay=0:{blur_y}"
        else:  # black
            # Black out bottom portion
            filter_complex = f"drawbox=x=0:y={blur_y}:w={width}:h={blur_h}:color=black:t=fill"
        
        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", filter_complex,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "copy",  # Keep original audio
            output_path
        ]
        
        print(f"🚀 Running FFmpeg ({method} mode)...")
        print(f"   Filter: {filter_complex}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for completion
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                print(f"✅ Video saved to: {output_path}")
                return True
            else:
                print(f"❌ FFmpeg error: {stderr[-500:]}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def set_subtitle_region(self, x: int, y: int, w: int, h: int):
        """Manually set subtitle region to remove."""
        self.subtitle_region = (x, y, w, h)
    
    def auto_detect_region(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Auto-detect subtitle region (usually bottom 15-20% of video).
        Returns (x, y, w, h) of detected region.
        """
        height, width = frame.shape[:2]
        
        # Subtitles are typically in bottom 15-20% of video
        y_start = int(height * 0.80)
        y_end = height
        x_start = int(width * 0.1)
        x_end = int(width * 0.9)
        
        return (x_start, y_start, x_end - x_start, y_end - y_start)
    
    def detect_text_mask(self, frame: np.ndarray, region: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Detect text in the given region and create a mask.
        Returns binary mask where text is white (255).
        """
        x, y, w, h = region
        roi = frame[y:y+h, x:x+w]
        
        # Convert to grayscale
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi
        
        # Enhance contrast
        gray = cv2.equalizeHist(gray)
        
        # Threshold to find bright text (subtitles are usually white/bright)
        _, text_mask = cv2.threshold(gray, self.detection_threshold, 255, cv2.THRESH_BINARY)
        
        # Dilate to connect text regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        text_mask = cv2.dilate(text_mask, kernel, iterations=2)
        
        # Create full-size mask
        full_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        full_mask[y:y+h, x:x+w] = text_mask
        
        return full_mask
    
    def remove_subtitles_frame(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Remove subtitles from a single frame using inpainting.
        """
        # Use OpenCV's inpainting
        result = cv2.inpaint(frame, mask, self.inpaint_radius, cv2.INPAINT_TELEA)
        return result
    
    def process_video(self, input_path: str, output_path: str, 
                      progress_callback=None, region: Tuple[int, int, int, int] = None) -> bool:
        """
        Process entire video and remove subtitles.
        
        Args:
            input_path: Path to input video
            output_path: Path to save output video
            progress_callback: Optional callback(current_frame, total_frames)
            region: Optional (x, y, w, h) for subtitle region. None = auto-detect
        
        Returns:
            True if successful, False otherwise
        """
        # Open video
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            print(f"Error: Cannot open video {input_path}")
            return False
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        print(f"🎬 Processing video: {total_frames} frames @ {fps}fps")
        print(f"📐 Resolution: {width}x{height}")
        
        # Auto-detect region from first frame if not specified
        ret, first_frame = cap.read()
        if not ret:
            print("Error: Cannot read first frame")
            return False
        
        if region is None:
            region = self.auto_detect_region(first_frame)
            print(f"📍 Auto-detected subtitle region: {region}")
        
        # Reset to beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect text mask in subtitle region
            mask = self.detect_text_mask(frame, region)
            
            # Remove subtitles if mask has content
            if np.any(mask):
                frame = self.remove_subtitles_frame(frame, mask)
            
            out.write(frame)
            frame_count += 1
            
            # Progress callback
            if progress_callback and frame_count % 30 == 0:  # Every second at 30fps
                progress_callback(frame_count, total_frames)
            
            # Print progress every 5%
            if frame_count % (total_frames // 20 + 1) == 0:
                percent = (frame_count / total_frames) * 100
                print(f"  ⏳ Progress: {percent:.1f}% ({frame_count}/{total_frames})")
        
        cap.release()
        out.release()
        
        print(f"✅ Video saved to: {output_path}")
        return True
    
    def remove_subtitles_simple(self, input_path: str, output_path: str,
                                  bottom_percent: float = 0.15) -> bool:
        """
        Simple subtitle removal by blacking out bottom portion.
        Fast but less sophisticated than inpainting.
        
        Args:
            input_path: Input video path
            output_path: Output video path
            bottom_percent: Percentage of video height to black out (default 15%)
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            return False
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        y_start = int(height * (1 - bottom_percent))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Black out bottom portion
            frame[y_start:, :] = (0, 0, 0)
            out.write(frame)
        
        cap.release()
        out.release()
        return True


# Global instance
subtitle_remover_service = SubtitleRemoverService()
