import unittest
import sys
import os
import shutil
import tempfile

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.ai.transcription import transcription_service
from src.core.ai.tts import tts_service

class TestAIFeatures(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_transcription_mock(self):
        # Create dummy file
        dummy_path = os.path.join(self.temp_dir, "test_video.mp4")
        with open(dummy_path, 'w') as f:
            f.write("dummy content")
            
        # Test mock transcription
        result = transcription_service.transcribe(dummy_path)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        self.assertIn("text", result[0])

    def test_tts_generation(self):
        # Test TTS generation
        output_path = os.path.join(self.temp_dir, "test_tts.wav")
        text = "Hello world this is a test"
        
        generated_path = tts_service.generate_speech(text, output_path)
        
        self.assertTrue(os.path.exists(generated_path))
        self.assertEqual(generated_path, output_path)
        
        # Check file size > 0 (it has headers + silence)
        self.assertTrue(os.path.getsize(generated_path) > 0)

if __name__ == '__main__':
    unittest.main()
