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
        
        try:
            # Use MLX Whisper if available
            if self.use_mlx:
                return self._transcribe_mlx(file_path, language)
            
            # Standard Whisper
            print("This may take several minutes depending on video length...")
            options = {"task": "transcribe"}
            if language:
                options["language"] = language
            
            result = self.model.transcribe(file_path, **options)
            
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
        
        # For other languages, use deep-translator
        print(f"[DEBUG] Translating {len(segments)} segments to '{target_language}' using GoogleTranslator...")
        
        try:
            from deep_translator import GoogleTranslator
            
            translated_segments = []
            
            for i, seg in enumerate(segments):
                original_text = seg["text"].strip()
                if not original_text:
                    translated_segments.append(seg)
                    continue
                    
                try:
                    # Try with auto-detect first
                    translator = GoogleTranslator(source='auto', target=target_language)
                    translated_text = translator.translate(original_text)
                    
                    # If translation returned same text, try with explicit Chinese source
                    if translated_text == original_text:
                        # Try Traditional Chinese
                        translator = GoogleTranslator(source='zh-TW', target=target_language)
                        translated_text = translator.translate(original_text)
                    
                    # If still same, try Simplified Chinese
                    if translated_text == original_text:
                        translator = GoogleTranslator(source='zh-CN', target=target_language)
                        translated_text = translator.translate(original_text)
                    
                    # Use translated if it's different and valid
                    if translated_text and translated_text.strip() and translated_text != original_text:
                        final_text = translated_text.strip()
                    else:
                        final_text = original_text
                        print(f"  ⚠️ [{i+1}] Could not translate: '{original_text[:30]}...'")
                    
                    translated_segments.append({
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": final_text
                    })
                    
                    # Debug: show translation progress
                    if i < 3 or (i + 1) % 10 == 0:
                        print(f"  [{i+1}/{len(segments)}] '{original_text[:20]}' -> '{final_text[:20]}'")
                        
                except Exception as e:
                    print(f"Translation error for segment {i}: {e}")
                    translated_segments.append({
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": original_text
                    })
            
            print(f"✅ Translation complete! {len(translated_segments)} segments translated to {target_language}.")
            return translated_segments
            
        except ImportError:
            print("❌ deep-translator not installed. Run: pip install deep-translator")
            return segments
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
