import os
import platform
from typing import List, Dict, Any, Optional

class TranscriptionService:
    def __init__(self):
        self.model = None
        self.model_name = "base"  # Options: tiny, base, small, medium, large
        self.use_mlx = False  # Will be set to True if MLX is available
        self._mlx_model = None

    def _is_apple_silicon(self) -> bool:
        """Check if running on Apple Silicon Mac."""
        return platform.system() == "Darwin" and platform.machine() == "arm64"

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
        Preprocess audio by converting to WAV format.
        This fixes issues with certain audio codecs that cause NaN errors in Whisper.
        """
        import subprocess
        import tempfile
        import hashlib
        
        # Create temp file path
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        temp_wav = os.path.join(tempfile.gettempdir(), f"whisper_audio_{file_hash}.wav")
        
        # If already preprocessed, return cached file
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
        
        # Preprocess audio to fix codec issues
        processed_file = self._preprocess_audio(file_path)
        
        try:
            # Use MLX Whisper if available
            if self.use_mlx:
                return self._transcribe_mlx(processed_file, language)
            
            # Standard Whisper
            print("This may take several minutes depending on video length...")
            options = {"task": "transcribe", "fp16": False}  # Disable fp16 to avoid NaN issues
            if language:
                options["language"] = language
            
            result = self.model.transcribe(processed_file, **options)
            
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
        
        options = {}
        if language:
            options["language"] = language
        
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
        
        # If target is English, use Whisper's built-in translation
        if target_language == "en":
            return self._transcribe_to_english(file_path)
        
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
            for i, seg in enumerate(segments):
                text = seg["text"].strip()
                if text:
                    valid_indices.append(i)
                    valid_texts.append(text)
            
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
            
            # Rebuild segments with translations
            translation_map = dict(zip(valid_indices, all_translations))
            
            for i, seg in enumerate(segments):
                original_text = seg["text"].strip()
                
                if i in translation_map:
                    translated_text = translation_map[i]
                    if translated_text and translated_text.strip():
                        final_text = translated_text.strip()
                    else:
                        final_text = original_text
                else:
                    final_text = original_text
                
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
