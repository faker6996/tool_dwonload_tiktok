"""
OCR Subtitle Extraction Service
Extract hardcoded subtitles from video frames using EasyOCR.
This is for videos with text overlays but no speech.
"""
import cv2
import os
from typing import List, Dict, Any, Optional, Tuple


class OCRSubtitleExtractor:
    """Extract subtitles from video frames using OCR."""
    
    def __init__(self):
        self._reader = None
        self._lang_set = None
    
    def _get_reader(self, lang_set: list):
        """Get or create EasyOCR reader."""
        if self._reader is None or self._lang_set != lang_set:
            import easyocr
            print(f"🔍 Loading EasyOCR model for {lang_set}...")
            self._reader = easyocr.Reader(lang_set, gpu=True, verbose=False)
            self._lang_set = lang_set
        return self._reader
    
    def extract_subtitles(
        self, 
        video_path: str, 
        target_lang: str = "vi",
        fps_sample: float = 1.0,  # Sample 1 frame per second
        bottom_percent: float = 1.0,  # Scan entire frame (text can be anywhere)
        min_confidence: float = 0.1,  # Lower threshold for better detection
        translate: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract subtitles from video using OCR.
        
        Args:
            video_path: Path to video file
            target_lang: Target language for translation
            fps_sample: How many frames per second to sample
            bottom_percent: Bottom percentage of frame to search for subtitles
            min_confidence: Minimum OCR confidence threshold
            translate: Whether to translate extracted text
            
        Returns:
            List of subtitle segments: {'start': float, 'end': float, 'text': str}
        """
        print(f"📖 Starting OCR subtitle extraction from: {os.path.basename(video_path)}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Cannot open video: {video_path}")
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps
        
        print(f"📐 Video: {width}x{height}, {fps:.1f}fps, {duration:.1f}s")
        
        # Calculate frame sampling
        frame_interval = int(fps / fps_sample)  # Sample every N frames
        if frame_interval < 1:
            frame_interval = 1
        
        sample_frames = list(range(0, total_frames, frame_interval))
        print(f"🎬 Sampling {len(sample_frames)} frames (every {frame_interval} frames)")
        
        # Try both Traditional and Simplified Chinese
        all_detections = []
        
        for lang_set in [['ch_tra', 'en'], ['ch_sim', 'en']]:
            try:
                reader = self._get_reader(lang_set)
                detections = []
                
                print(f"🔍 OCR scanning with {lang_set[0]}...")
                
                for i, frame_idx in enumerate(sample_frames):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    if not ret:
                        continue
                    
                    # Calculate timestamp
                    timestamp = frame_idx / fps
                    
                    # Extract bottom portion where subtitles usually are
                    search_y = int(height * (1 - bottom_percent))
                    roi = frame[search_y:, :]
                    
                    # OCR the region
                    results = reader.readtext(roi)
                    
                    frame_texts = []
                    for (bbox, text, prob) in results:
                        if prob >= min_confidence and text.strip():
                            frame_texts.append(text.strip())
                            print(f"    📝 Detected: '{text[:30]}...' (conf: {prob:.2f})")
                    
                    if frame_texts:
                        combined_text = ' '.join(frame_texts)
                        detections.append({
                            'frame': frame_idx,
                            'time': timestamp,
                            'text': combined_text
                        })
                    
                    # Progress
                    if (i + 1) % 10 == 0:
                        print(f"  Progress: {i+1}/{len(sample_frames)} frames")
                
                if detections:
                    print(f"✅ Found {len(detections)} text occurrences using {lang_set[0]}")
                    all_detections = detections
                    break
                    
            except Exception as e:
                print(f"⚠️ Error with {lang_set}: {e}")
                continue
        
        cap.release()
        
        if not all_detections:
            print("⚠️ No subtitles detected in video")
            return []
        
        # Group similar consecutive texts into segments
        segments = self._group_into_segments(all_detections, frame_interval / fps)
        
        print(f"📝 Created {len(segments)} subtitle segments")
        
        # Translate if requested
        if translate and target_lang:
            segments = self._translate_segments(segments, target_lang)
        
        return segments
    
    def _group_into_segments(
        self, 
        detections: List[Dict], 
        time_gap: float
    ) -> List[Dict[str, Any]]:
        """
        Group consecutive detections with same/similar text into segments.
        """
        if not detections:
            return []
        
        segments = []
        current_segment = {
            'start': detections[0]['time'],
            'end': detections[0]['time'] + time_gap,
            'text': detections[0]['text']
        }
        
        for i in range(1, len(detections)):
            det = detections[i]
            prev_det = detections[i-1]
            
            # Check if text is similar (>50% overlap)
            similarity = self._text_similarity(current_segment['text'], det['text'])
            time_diff = det['time'] - prev_det['time']
            
            if similarity > 0.5 and time_diff < time_gap * 2:
                # Extend current segment
                current_segment['end'] = det['time'] + time_gap
                # Use the longer text version
                if len(det['text']) > len(current_segment['text']):
                    current_segment['text'] = det['text']
            else:
                # Save current segment and start new one
                if current_segment['text'].strip():
                    segments.append(current_segment)
                current_segment = {
                    'start': det['time'],
                    'end': det['time'] + time_gap,
                    'text': det['text']
                }
        
        # Don't forget last segment
        if current_segment['text'].strip():
            segments.append(current_segment)
        
        return segments
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity ratio."""
        if not text1 or not text2:
            return 0.0
        
        # Simple character overlap ratio
        set1 = set(text1)
        set2 = set(text2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _translate_segments(
        self, 
        segments: List[Dict], 
        target_lang: str
    ) -> List[Dict[str, Any]]:
        """Translate segment texts to target language."""
        if not segments:
            return segments
        
        try:
            from .translation import translation_service
            
            texts = [seg['text'] for seg in segments]
            print(f"🌐 Translating {len(texts)} segments to {target_lang}...")
            
            # Batch translate
            translated = translation_service.translate_batch(
                texts, 
                target_lang=target_lang, 
                source_lang="auto"
            )
            
            # Update segments with translations
            for i, seg in enumerate(segments):
                if i < len(translated) and translated[i]:
                    seg['text'] = translated[i]
            
            print(f"✅ Translation complete!")
            
        except Exception as e:
            print(f"⚠️ Translation error: {e}")
        
        return segments


# Global instance
ocr_subtitle_extractor = OCRSubtitleExtractor()
