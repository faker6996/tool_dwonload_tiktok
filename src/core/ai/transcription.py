import os
from typing import List, Dict, Any

class TranscriptionService:
    def __init__(self):
        self.model = None
        self.model_name = "base"  # Options: tiny, base, small, medium, large

    def load_model(self):
        """
        Load Whisper model.
        """
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
            # Transcribe with Whisper
            options = {"task": "transcribe"}
            if language:
                options["language"] = language
            
            result = self.model.transcribe(file_path, **options)
            
            # Convert to our format
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

# Global instance
transcription_service = TranscriptionService()
