import os
import time
from typing import List, Dict, Any

class TranscriptionService:
    def __init__(self):
        self.model = None

    def load_model(self):
        """
        Load Whisper model. 
        For MVP, we simulate this or load a small model if libraries are present.
        """
        print("Loading Transcription Model...")
        # In a real impl: import whisper; self.model = whisper.load_model("base")
        time.sleep(1) # Simulate loading
        self.model = "mock_model"

    def transcribe(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe audio file to segments.
        Returns list of dicts: {'start': float, 'end': float, 'text': str}
        """
        if not os.path.exists(file_path):
            return []

        if not self.model:
            self.load_model()

        print(f"Transcribing {file_path}...")
        # Simulate transcription delay
        time.sleep(2)
        
        # Mock result for verification
        return [
            {"start": 0.0, "end": 2.0, "text": "Hello, welcome to the video."},
            {"start": 2.5, "end": 4.0, "text": "This is an auto-generated caption."},
            {"start": 4.5, "end": 6.0, "text": "AI is amazing!"}
        ]

# Global instance
transcription_service = TranscriptionService()
