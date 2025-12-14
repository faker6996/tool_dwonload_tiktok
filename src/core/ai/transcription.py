import os
from typing import List, Dict, Any, Optional

class TranscriptionService:
    def __init__(self):
        self.model = None
        self.model_name = "base"  # Options: tiny, base, small, medium, large

    def load_model(self):
        """Load Whisper model."""
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

        if not self.model:
            self.load_model()

        print(f"Transcribing {file_path}...")
        print("This may take several minutes depending on video length...")
        
        try:
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

    def transcribe_and_translate(self, file_path: str, target_language: str = "vi") -> List[Dict[str, Any]]:
        """
        Transcribe audio/video and translate to target language.
        
        Args:
            file_path: Path to audio/video file
            target_language: Target language code (vi, en, zh, ja, ko, etc.)
            
        Returns:
            List of translated segments: {'start': float, 'end': float, 'text': str}
        """
        # First transcribe in original language
        segments = self.transcribe(file_path, language=None)  # Auto-detect
        
        if not segments:
            return []
        
        # If target is English, use Whisper's built-in translation
        if target_language == "en":
            return self._transcribe_to_english(file_path)
        
        # For other languages, use deep-translator
        print(f"Translating {len(segments)} segments to '{target_language}'...")
        
        try:
            from deep_translator import GoogleTranslator
            
            translator = GoogleTranslator(source='auto', target=target_language)
            translated_segments = []
            
            for i, seg in enumerate(segments):
                try:
                    translated_text = translator.translate(seg["text"])
                    translated_segments.append({
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": translated_text or seg["text"]
                    })
                    
                    if (i + 1) % 20 == 0:
                        print(f"Translated {i + 1}/{len(segments)} segments...")
                        
                except Exception as e:
                    print(f"Translation error for segment {i}: {e}")
                    translated_segments.append(seg)  # Keep original if translation fails
            
            print(f"Translation complete! {len(translated_segments)} segments translated.")
            return translated_segments
            
        except ImportError:
            print("deep-translator not installed. Run: pip install deep-translator")
            return segments
        except Exception as e:
            print(f"Translation error: {e}")
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
