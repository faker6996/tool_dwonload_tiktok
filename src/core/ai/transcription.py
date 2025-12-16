import os
import platform
from typing import List, Dict, Any, Optional

class TranscriptionService:
    def __init__(self):
        self.model = None
        self.model_name = "small"  # Options: tiny, base, small, medium, large (small is good for Chinese)
        self.use_mlx = False  # Will be set to True if MLX is available
        
        # OpenAI Whisper API support
        self.use_openai_api = False  # If True, use cloud API instead of local
        self._openai_api_key = None

    def _is_apple_silicon(self) -> bool:
        """Check if running on Apple Silicon Mac."""
        return platform.system() == "Darwin" and platform.machine() == "arm64"
    
    def set_openai_api_key(self, api_key: str):
        """Set OpenAI API key for cloud Whisper."""
        self._openai_api_key = api_key
        print(f"✅ OpenAI Whisper API key set")
    
    def set_use_openai_api(self, use_api: bool):
        """Toggle between local Whisper and OpenAI API."""
        self.use_openai_api = use_api
        if use_api:
            print("☁️ Whisper mode: OpenAI API")
        else:
            print("💻 Whisper mode: Local")

    def load_model(self):
        """Load Whisper model - prioritize MLX on Apple Silicon."""
        
        # Try MLX Whisper first on Apple Silicon
        if self._is_apple_silicon():
            try:
                import mlx_whisper
                print(f"🚀 Apple Silicon detected! Using MLX Whisper for fast transcription...")
                self.use_mlx = True
                # MLX Whisper loads model on-demand, no need to preload
                print("✅ MLX Whisper ready!")
                return
            except ImportError:
                print("⚠️ MLX Whisper not installed. Install with: pip install mlx-whisper")
                print("   Falling back to standard Whisper (slower)...")
        
        # Fallback to standard Whisper
        import whisper
        print(f"Loading Whisper model '{self.model_name}'... (this may take a while on first run)")
        self.model = whisper.load_model(self.model_name)
        print("Model loaded successfully!")

    def _preprocess_audio(self, file_path: str) -> str:
        """
        Preprocess audio by converting to WAV format for local Whisper.
        This fixes issues with certain audio codecs that cause NaN errors in Whisper.
        """
        import subprocess
        import tempfile
        import hashlib
        
        # Create cache key based on path + mtime + size (not just path)
        st = os.stat(file_path)
        cache_key = f"{file_path}:{st.st_mtime}:{st.st_size}"
        file_hash = hashlib.md5(cache_key.encode()).hexdigest()[:8]
        temp_wav = os.path.join(tempfile.gettempdir(), f"whisper_audio_{file_hash}.wav")
        
        # If already preprocessed with same file, return cached
        if os.path.exists(temp_wav):
            return temp_wav
        
        print("🔊 Preprocessing audio for Whisper...")
        
        try:
            # Convert to 16kHz mono WAV (optimal for Whisper)
            cmd = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # 16-bit PCM
                "-ar", "16000",  # 16kHz sample rate
                "-ac", "1",  # Mono
                temp_wav
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 1000:
                print("✅ Audio preprocessed successfully!")
                return temp_wav
            else:
                print("⚠️ Audio preprocessing failed, using original file")
                return file_path
                
        except Exception as e:
            print(f"⚠️ FFmpeg preprocessing error: {e}")
            return file_path
    
    def _preprocess_audio_for_openai(self, file_path: str) -> str:
        """
        Preprocess audio to MP3 for OpenAI API (much smaller than WAV).
        OpenAI limit is 25MB - MP3 is ~10x smaller than WAV.
        """
        import subprocess
        import tempfile
        import hashlib
        
        st = os.stat(file_path)
        cache_key = f"openai:{file_path}:{st.st_mtime}:{st.st_size}"
        file_hash = hashlib.md5(cache_key.encode()).hexdigest()[:8]
        temp_mp3 = os.path.join(tempfile.gettempdir(), f"whisper_openai_{file_hash}.mp3")
        
        if os.path.exists(temp_mp3):
            return temp_mp3
        
        print("🔊 Preprocessing audio for OpenAI API (mp3)...")
        
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-vn",
                "-acodec", "libmp3lame",
                "-ar", "16000",
                "-ac", "1",
                "-b:a", "64k",  # Low bitrate for small file
                temp_mp3
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 1000:
                size_mb = os.path.getsize(temp_mp3) / 1024 / 1024
                print(f"✅ Audio preprocessed for OpenAI: {size_mb:.1f}MB")
                return temp_mp3
            else:
                print("⚠️ MP3 preprocessing failed, using original")
                return file_path
                
        except Exception as e:
            print(f"⚠️ FFmpeg error: {e}")
            return file_path

    def transcribe(self, file_path: str, language: str = None) -> List[Dict[str, Any]]:
        """
        Transcribe audio/video file to segments.
        Returns list of dicts: {'start': float, 'end': float, 'text': str}
        
        Args:
            file_path: Path to audio/video file
            language: Language code (e.g. 'en', 'vi', 'zh'). None = auto-detect
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return []

        if not self.model and not self.use_mlx:
            self.load_model()

        print(f"Transcribing {file_path}...")
        
        # Keep original for fallback
        original_file = file_path
        
        try:
            # Use OpenAI API if enabled - preprocess to mp3 (smaller)
            if self.use_openai_api and self._openai_api_key:
                processed_mp3 = self._preprocess_audio_for_openai(original_file)
                result = self._transcribe_openai(processed_mp3, language)
                if result:
                    return result
                # Fallback to local - continue below
                print("⚠️ OpenAI failed, falling back to local Whisper...")
            
            # Local Whisper - preprocess to WAV
            processed_wav = self._preprocess_audio(original_file)
            
            # Use MLX Whisper if available
            if self.use_mlx:
                return self._transcribe_mlx(processed_wav, language)
            
            # Standard Whisper
            print("This may take several minutes depending on video length...")
            options = {"task": "transcribe", "fp16": False}  # Disable fp16 to avoid NaN issues
            if language:
                options["language"] = language
            
            result = self.model.transcribe(processed_wav, **options)
            
            segments = []
            for seg in result.get("segments", []):
                segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                })
            
            print(f"Transcription complete! Found {len(segments)} segments.")
            return segments
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return []

    def _transcribe_mlx(self, file_path: str, language: str = None) -> List[Dict[str, Any]]:
        """Transcribe using MLX Whisper (Apple Silicon optimized)."""
        import mlx_whisper
        
        print("⚡ Transcribing with MLX Whisper (Apple Silicon accelerated)...")
        
        # MLX Whisper model path format
        model_path = f"mlx-community/whisper-{self.model_name}-mlx"
        
        options = {
            "word_timestamps": True,  # Better segmentation
            "condition_on_previous_text": True,  # Helps with context
        }
        if language:
            options["language"] = language
        else:
            # For auto-detect, hint that it might be Chinese
            options["language"] = None  # Let Whisper detect
        
        result = mlx_whisper.transcribe(
            file_path,
            path_or_hf_repo=model_path,
            **options
        )
        
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip()
            })
        
        print(f"✅ MLX Transcription complete! Found {len(segments)} segments.")
        return segments
    
    def _transcribe_openai(self, file_path: str, language: str = None) -> List[Dict[str, Any]]:
        """Transcribe using OpenAI Whisper API (cloud)."""
        import httpx
        import json
        
        print("☁️ Transcribing with OpenAI Whisper API...")
        
        # OpenAI Whisper API endpoint
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self._openai_api_key}"
        }
        
        # Prepare form data
        data = {
            "model": "whisper-1",
            "response_format": "verbose_json",
            "timestamp_granularities[]": "segment",
            "temperature": 0,  # Deterministic output (integer, not string)
            "prompt": "Transcribe spoken dialogue only. Ignore singing, lyrics, and background music."
        }
        if language:
            data["language"] = language
        
        try:
            # Check file size (OpenAI limit: 25MB)
            file_size = os.path.getsize(file_path)
            if file_size > 25 * 1024 * 1024:
                print(f"⚠️ File too large ({file_size / 1024 / 1024:.1f}MB). OpenAI limit is 25MB.")
                return []  # Return empty, caller will fallback to local
            
            # Auto-detect content type based on extension
            ext = os.path.splitext(file_path)[1].lower()
            content_types = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4"}
            content_type = content_types.get(ext, "audio/mpeg")
            
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, content_type)}
                
                with httpx.Client(timeout=300.0) as client:
                    response = client.post(url, headers=headers, data=data, files=files)
                
                if response.status_code != 200:
                    error_msg = response.json().get("error", {}).get("message", response.text)
                    print(f"❌ OpenAI API error: {error_msg}")
                    return []  # Return empty, caller will fallback
                
                result = response.json()
            
            segments = []
            for seg in result.get("segments", []):
                segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                })
            
            print(f"✅ OpenAI Transcription complete! Found {len(segments)} segments.")
            return segments
            
        except Exception as e:
            print(f"❌ OpenAI Whisper error: {e}")
            return []  # Return empty, caller will fallback to local

    def transcribe_and_translate(self, file_path: str, target_language: str = "vi") -> List[Dict[str, Any]]:
        """
        Transcribe audio/video and translate to target language.
        
        Args:
            file_path: Path to audio/video file
            target_language: Target language code (vi, en, zh, ja, ko, etc.)
            
        Returns:
            List of translated segments: {'start': float, 'end': float, 'text': str}
        """
        print(f"[DEBUG] transcribe_and_translate called with target_language={target_language}")
        
        # First transcribe in original language
        segments = self.transcribe(file_path, language=None)  # Auto-detect
        
        if not segments:
            return []
        
        # NOTE: Removed special case for English (target_language == "en")
        # because it crashes on MLX mode (self.model is None)
        # Now we use translation_service for ALL languages including English
        
        # Use TranslationService for translation
        from .translation import translation_service
        
        provider_name = translation_service.get_provider_name()
        print(f"🚀 Translating {len(segments)} segments to '{target_language}' using {provider_name}...")
        
        try:
            # Batch translation for speed - 20 segments per batch
            BATCH_SIZE = 20
            translated_segments = []
            
            # Filter out empty segments and track indices
            valid_indices = []
            valid_texts = []
            empty_count = 0
            whitespace_only = 0
            too_short = 0
            
            MIN_TEXT_LENGTH = 2  # Minimum chars to be considered valid
            MIN_DURATION = 0.3  # Minimum seconds
            
            for i, seg in enumerate(segments):
                text = seg.get("text", "")
                if not text:
                    empty_count += 1
                    continue
                text = text.strip()
                if not text:
                    whitespace_only += 1
                    continue
                # Filter too-short segments
                duration = seg.get("end", 0) - seg.get("start", 0)
                if len(text) < MIN_TEXT_LENGTH or duration < MIN_DURATION:
                    too_short += 1
                    continue
                valid_indices.append(i)
                valid_texts.append(text)
            
            # Debug: show filtering stats
            total = len(segments)
            valid = len(valid_texts)
            print(f"📊 Segment stats: {total} total → {valid} valid ({empty_count} empty, {whitespace_only} whitespace, {too_short} too-short)")
            
            if valid_texts:
                # Show sample of texts
                print(f"📝 Sample texts: {valid_texts[:3]}")
            
            print(f"📦 Processing {len(valid_texts)} non-empty segments in batches of {BATCH_SIZE}...")
            
            # Prepare all batches
            batches = []
            for batch_start in range(0, len(valid_texts), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(valid_texts))
                batch_texts = valid_texts[batch_start:batch_end]
                batches.append((batch_start, batch_texts))
            
            total_batches = len(batches)
            print(f"⚡ Running {total_batches} batches in PARALLEL (2 workers)...")
            
            # Parallel translation using ThreadPoolExecutor
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import time
            
            def translate_batch_worker(args):
                batch_idx, batch_texts = args
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                try:
                    result = translation_service.translate_batch(
                        batch_texts,
                        target_lang=target_language,
                        source_lang="auto"
                    )
                    return (batch_idx, result)
                except Exception as e:
                    print(f"  ⚠️ Batch {batch_idx} error: {e}")
                    return (batch_idx, batch_texts)  # Return original on error
            
            # Run batches in parallel with 2 workers (safer for API limits)
            all_translations = [None] * len(valid_texts)
            completed = 0
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {executor.submit(translate_batch_worker, batch): batch for batch in batches}
                
                for future in as_completed(futures):
                    batch_start, batch_results = future.result()
                    
                    # Store results at correct positions
                    for i, result in enumerate(batch_results):
                        if batch_start + i < len(all_translations):
                            all_translations[batch_start + i] = result
                    
                    completed += 1
                    print(f"  ✅ Completed {completed}/{total_batches} batches")
            
            # Rebuild segments with translations - ONLY include filtered segments
            valid_set = set(valid_indices)
            translation_map = dict(zip(valid_indices, all_translations))
            
            for i, seg in enumerate(segments):
                # Skip segments that didn't pass filter
                if i not in valid_set:
                    continue
                
                original_text = seg["text"].strip()
                translated_text = translation_map.get(i, original_text)
                
                final_text = translated_text.strip() if translated_text else original_text
                
                # Only add segments with non-empty text
                if final_text and final_text.strip():
                    translated_segments.append({
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": final_text
                    })
            
            # Show sample translations
            print(f"\n📝 Sample translations:")
            for i in range(min(5, len(valid_texts))):
                orig = valid_texts[i][:25]
                trans = all_translations[i][:25] if i < len(all_translations) else "N/A"
                print(f"  '{orig}...' -> '{trans}...'")
            
            print(f"\n✅ Translation complete! {len(translated_segments)} segments translated to {target_language}.")
            return translated_segments
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            return segments

    def _transcribe_to_english(self, file_path: str) -> List[Dict[str, Any]]:
        """Use Whisper's built-in translation to English."""
        if not self.model:
            self.load_model()
            
        print("Translating to English using Whisper...")
        
        try:
            result = self.model.transcribe(file_path, task="translate")
            
            segments = []
            for seg in result.get("segments", []):
                segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                })
            
            return segments
            
        except Exception as e:
            print(f"Translation error: {e}")
            return []

# Global instance
transcription_service = TranscriptionService()
