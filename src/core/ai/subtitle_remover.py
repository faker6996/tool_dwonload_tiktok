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
        self._gpu_encoder = None  # Cache GPU detection result
    
    def _detect_gpu(self) -> dict:
        """Auto-detect GPU and return best encoder settings."""
        if self._gpu_encoder is not None:
            return self._gpu_encoder
        
        import subprocess
        
        # Check NVIDIA GPU
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, timeout=5)
            if result.returncode == 0:
                # Check if h264_nvenc is available in ffmpeg
                ffmpeg_check = subprocess.run(
                    ['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=5
                )
                if 'h264_nvenc' in ffmpeg_check.stdout:
                    print("🎮 NVIDIA GPU detected - using NVENC acceleration")
                    self._gpu_encoder = {
                        "encoder": "h264_nvenc",
                        "preset": ["-preset", "p4"],
                        # Use constrained quality with bitrate limit to avoid large files
                        "extra": ["-cq", "28", "-maxrate", "2M", "-bufsize", "4M"],
                    }
                    return self._gpu_encoder
        except:
            pass
        
        # Check AMD GPU (Linux)
        try:
            ffmpeg_check = subprocess.run(
                ['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=5
            )
            if 'h264_amf' in ffmpeg_check.stdout:
                print("🎮 AMD GPU detected - using AMF acceleration")
                self._gpu_encoder = {
                    "encoder": "h264_amf",
                    "preset": ["-quality", "speed"],
                    "extra": [],
                }
                return self._gpu_encoder
        except:
            pass
        
        # Check Intel QuickSync
        try:
            ffmpeg_check = subprocess.run(
                ['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=5
            )
            if 'h264_qsv' in ffmpeg_check.stdout:
                print("🎮 Intel GPU detected - using QuickSync acceleration")
                self._gpu_encoder = {
                    "encoder": "h264_qsv",
                    "preset": ["-preset", "fast"],
                    "extra": [],
                }
                return self._gpu_encoder
        except:
            pass
        
        # Check Apple Silicon (M1/M2/M3) VideoToolbox
        try:
            import platform
            if platform.system() == 'Darwin':  # macOS
                ffmpeg_check = subprocess.run(
                    ['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=5
                )
                if 'h264_videotoolbox' in ffmpeg_check.stdout:
                    print("🍎 Apple Silicon detected - using VideoToolbox acceleration")
                    self._gpu_encoder = {
                        "encoder": "h264_videotoolbox",
                        "preset": [],  # VideoToolbox has different options
                        "extra": ["-q:v", "60"],  # Quality 1-100 (higher = better)
                    }
                    return self._gpu_encoder
        except:
            pass
        
        # Fallback to CPU
        print("💻 No GPU acceleration found - using CPU encoding")
        self._gpu_encoder = {
            "encoder": "libx264",
            "preset": ["-preset", "fast"],
            "extra": ["-crf", "23"],
        }
        return self._gpu_encoder
    
    def detect_subtitle_region_easyocr(self, video_path: str, num_samples: int = 10) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect subtitle region using EasyOCR for accurate text detection.
        
        Returns (x, y, w, h) of detected subtitle region, or None if not found.
        """
        try:
            import easyocr
        except ImportError:
            print("⚠️ EasyOCR not installed, falling back to OpenCV")
            return self.detect_subtitle_region_opencv(video_path, num_samples)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Cannot open video: {video_path}")
            return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Try Traditional Chinese first (common for TikTok/Douyin from Taiwan/HK)
        # If no results, try Simplified Chinese (Mainland China)
        print("🔍 Loading EasyOCR model (first time may take a while)...")
        
        all_text_boxes = []
        
        for lang_set in [['ch_tra', 'en'], ['ch_sim', 'en']]:
            try:
                reader = easyocr.Reader(lang_set, gpu=True, verbose=False)
                
                # Sample frames
                sample_positions = [int(total_frames * (0.2 + 0.6 * i / (num_samples - 1))) for i in range(num_samples)]
                
                print(f"🔍 Detecting subtitles with EasyOCR ({lang_set[0]}) in {num_samples} frames...")
                
                for i, frame_pos in enumerate(sample_positions):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                    ret, frame = cap.read()
                    if not ret:
                        continue
                    
                    # Scan entire frame (text can be anywhere)
                    search_y = 0
                    roi = frame  # Use full frame
                    
                    # Detect text with EasyOCR
                    results = reader.readtext(roi)
                    
                    for (bbox, text, prob) in results:
                        if prob > 0.1 and text.strip():  # Lower threshold, ensure non-empty text
                            # bbox is [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                            x1, y1 = int(bbox[0][0]), int(bbox[0][1])
                            x2, y2 = int(bbox[2][0]), int(bbox[2][1])
                            w, h = x2 - x1, y2 - y1
                            
                            # Convert back to full frame coordinates
                            all_text_boxes.append((x1, y1 + search_y, w, h))
                            print(f"    📝 Detected: '{text[:30]}...' (conf: {prob:.2f})")
                    
                    print(f"  Frame {i+1}/{num_samples}: Found {len(results)} text regions")
                
                # If found results, break out of loop
                if all_text_boxes:
                    print(f"✅ Found {len(all_text_boxes)} text regions using {lang_set[0]}")
                    break
            except Exception as e:
                print(f"⚠️ Error with {lang_set}: {e}")
                continue
        
        cap.release()
        
        if not all_text_boxes:
            print("⚠️ No subtitle regions detected by EasyOCR")
            return None
        
        # Combine all detected boxes into one bounding box
        min_x = min(box[0] for box in all_text_boxes)
        min_y = min(box[1] for box in all_text_boxes)
        max_x = max(box[0] + box[2] for box in all_text_boxes)
        max_y = max(box[1] + box[3] for box in all_text_boxes)
        
        # Add small padding
        padding_x = int(width * 0.02)
        padding_y = int(height * 0.01)
        
        final_x = max(0, min_x - padding_x)
        final_y = max(0, min_y - padding_y)
        final_w = min(width - final_x, max_x - min_x + padding_x * 2)
        final_h = min(height - final_y, max_y - min_y + padding_y * 2)
        
        print(f"✅ EasyOCR detected subtitle region: x={final_x}, y={final_y}, w={final_w}, h={final_h}")
        return (final_x, final_y, final_w, final_h)
    
    def detect_subtitle_region_opencv(self, video_path: str, num_samples: int = 5) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect subtitle region by sampling multiple frames using OpenCV.
        
        Returns (x, y, w, h) of detected subtitle region, or None if not found.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Cannot open video: {video_path}")
            return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Sample frames at different positions (skip first and last 5%)
        sample_positions = [int(total_frames * (0.1 + 0.8 * i / (num_samples - 1))) for i in range(num_samples)]
        
        all_text_boxes = []
        
        print(f"🔍 Detecting subtitles in {num_samples} frames...")
        
        for i, frame_pos in enumerate(sample_positions):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Only search in bottom 30% of frame (where subtitles usually are)
            search_y = int(height * 0.70)
            roi = frame[search_y:, :]
            
            # Convert to grayscale
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to find bright text (subtitles are usually white/bright)
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                # Filter: text regions should have certain aspect ratio and size
                if w > 20 and h > 10 and w > h * 2:  # Wide rectangles (text lines)
                    # Convert back to full frame coordinates
                    all_text_boxes.append((x, y + search_y, w, h))
            
            print(f"  Frame {i+1}/{num_samples}: Found {len(contours)} potential text regions")
        
        cap.release()
        
        if not all_text_boxes:
            print("⚠️ No subtitle regions detected, using default position")
            return None
        
        # Combine all detected boxes into one bounding box
        min_x = min(box[0] for box in all_text_boxes)
        min_y = min(box[1] for box in all_text_boxes)
        max_x = max(box[0] + box[2] for box in all_text_boxes)
        max_y = max(box[1] + box[3] for box in all_text_boxes)
        
        # Calculate subtitle dimensions - constrain to centered area
        sub_width = max_x - min_x
        sub_height = max_y - min_y
        
        # Limit maximum width to 60% of video (subtitles shouldn't be wider)
        max_allowed_width = int(width * 0.6)
        if sub_width > max_allowed_width:
            center_x = (min_x + max_x) // 2
            min_x = center_x - max_allowed_width // 2
            sub_width = max_allowed_width
        
        # Limit maximum height to 12% of video (subtitles are usually 1-2 lines)
        max_allowed_height = int(height * 0.12)
        if sub_height > max_allowed_height:
            # Keep bottom portion (subtitles are at bottom)
            min_y = max_y - max_allowed_height
            sub_height = max_allowed_height
        
        # Add padding - more on top to ensure full coverage
        padding_x = int(width * 0.02)  # 2% horizontal
        padding_y_top = int(height * 0.03)  # 3% top padding (more to cover text above)
        padding_y_bottom = int(height * 0.01)  # 1% bottom padding
        
        final_x = max(0, min_x - padding_x)
        final_y = max(0, min_y - padding_y_top)  # Move up more
        final_w = min(width - final_x, sub_width + padding_x * 2)
        final_h = min(height - final_y, sub_height + padding_y_top + padding_y_bottom)
        
        print(f"✅ Detected subtitle region: x={final_x}, y={final_y}, w={final_w}, h={final_h}")
        return (final_x, final_y, final_w, final_h)
    
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
        
        # Try to detect subtitle region using EasyOCR (only for blur/black, not crop)
        detected_region = None
        if method in ["blur", "black"]:
            print("🔍 Detecting subtitle position with EasyOCR...")
            detected_region = self.detect_subtitle_region_easyocr(input_path, num_samples=10)
        
        if detected_region:
            # Use detected region
            sub_x, sub_y, sub_width, sub_height = detected_region
            print(f"✅ Using detected region: {sub_x},{sub_y} -> {sub_width}x{sub_height}")
        else:
            # Fallback to default centered area (middle 70% width, bottom 12%)
            sub_height = int(height * min(bottom_percent, 0.12))
            sub_y = int(height * (1 - min(bottom_percent, 0.15)))
            sub_width = int(width * 0.7)
            sub_x = int(width * 0.15)
            print(f"⚠️ Using default region: {sub_x},{sub_y} -> {sub_width}x{sub_height}")
        
        if method == "crop":
            # Crop video to remove bottom portion
            crop_height = int(height * (1 - bottom_percent))
            filter_complex = f"crop=w={width}:h={crop_height}:x=0:y=0"
        elif method == "blur":
            # Blur only the detected/default subtitle area
            filter_complex = f"[0:v]split[main][blur];[blur]crop={sub_width}:{sub_height}:{sub_x}:{sub_y},boxblur=15:15[blurred];[main][blurred]overlay={sub_x}:{sub_y}"
        else:  # black
            # Black out only the detected/default subtitle area
            filter_complex = f"drawbox=x={sub_x}:y={sub_y}:w={sub_width}:h={sub_height}:color=black:t=fill"
        
        # Get GPU encoder settings
        gpu_settings = self._detect_gpu()
        encoder = gpu_settings["encoder"]
        
        # Build FFmpeg command with GPU acceleration
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", filter_complex,
            "-c:v", encoder,
        ]
        cmd.extend(gpu_settings["preset"])
        cmd.extend(gpu_settings["extra"])
        cmd.extend(["-c:a", "copy", output_path])
        
        print(f"🚀 Running FFmpeg ({method} mode) with {encoder}...")
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
