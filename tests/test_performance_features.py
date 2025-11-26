import unittest
import sys
import os
import shutil
import tempfile

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.settings.shortcuts import shortcut_manager
from src.core.ingestion import MediaIngestion

class TestPerformanceFeatures(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_shortcut_manager(self):
        # Test loading defaults
        self.assertIn("undo", shortcut_manager.shortcuts)
        self.assertEqual(shortcut_manager.get_shortcut("undo"), "Ctrl+Z")
        
        # Test setting shortcut
        shortcut_manager.set_shortcut("undo", "Ctrl+U")
        self.assertEqual(shortcut_manager.get_shortcut("undo"), "Ctrl+U")

    def test_proxy_generation_mock(self):
        ingestion = MediaIngestion()
        
        # Create dummy video file
        video_path = os.path.join(self.temp_dir, "test.mp4")
        with open(video_path, 'w') as f:
            f.write("video data")
            
        # Test generate_proxy
        proxy_path = ingestion.generate_proxy(video_path)
        
        self.assertTrue(os.path.exists(proxy_path))
        self.assertTrue(proxy_path.endswith("_proxy.mp4"))

if __name__ == '__main__':
    unittest.main()
