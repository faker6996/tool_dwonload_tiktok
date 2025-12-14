import os
import asyncio
import tempfile
from typing import Optional

class TTSService:
    def __init__(self):
        # Default voices for different languages
        self.voices = {
            "vi": "vi-VN-HoaiMyNeural",     # Vietnamese female
            "vi-male": "vi-VN-NamMinhNeural", # Vietnamese male
            "en": "en-US-AriaNeural",       # English female
            "en-male": "en-US-GuyNeural",   # English male
            "zh": "zh-CN-XiaoxiaoNeural",   # Chinese female
        }
        self.default_voice = "vi-VN-HoaiMyNeural"  # Default to Vietnamese

    def set_voice(self, voice_name: str):
        """Set the voice to use for TTS."""
        self.default_voice = voice_name

    def generate_speech(self, text: str, output_path: str, voice: str = None, rate: str = "+0%", pitch: str = "+0Hz") -> str:
        """
        Generate speech from text using edge-tts.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file (mp3)
            voice: Voice name (e.g., "vi-VN-HoaiMyNeural")
            rate: Speech rate (e.g., "+10%" for faster, "-10%" for slower)
            pitch: Voice pitch (e.g., "+5Hz" for higher)
            
        Returns:
            Path to the generated audio file
        """
        if not output_path.endswith('.mp3'):
            output_path = output_path.rsplit('.', 1)[0] + '.mp3'
            
        voice = voice or self.default_voice
        
        print(f"Generating speech for: '{text[:50]}...' with voice: {voice}")
        
        # Run async function in sync context
        asyncio.run(self._generate_async(text, output_path, voice, rate, pitch))
        
        print(f"Speech generated: {output_path}")
        return output_path

    async def _generate_async(self, text: str, output_path: str, voice: str, rate: str, pitch: str):
        """Async implementation using edge-tts."""
        import edge_tts
        
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(output_path)

    def get_available_voices(self, language: str = None) -> list:
        """
        Get list of available voices.
        
        Args:
            language: Filter by language code (e.g., "vi", "en", "zh")
            
        Returns:
            List of voice dictionaries
        """
        async def _get_voices():
            import edge_tts
            voices = await edge_tts.list_voices()
            if language:
                voices = [v for v in voices if v["Locale"].startswith(language)]
            return voices
        
        return asyncio.run(_get_voices())

    def get_voice_for_language(self, lang_code: str) -> str:
        """Get default voice for a language code."""
        return self.voices.get(lang_code, self.default_voice)

# Global instance
tts_service = TTSService()
