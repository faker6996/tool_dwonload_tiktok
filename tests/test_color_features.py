import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.timeline.clip import Clip

class TestColorFeatures(unittest.TestCase):
    def setUp(self):
        self.clip = Clip("c1", "Video Clip", duration=10.0)

    def test_color_properties_default(self):
        self.assertEqual(self.clip.brightness, 0.0)
        self.assertEqual(self.clip.contrast, 1.0)
        self.assertEqual(self.clip.saturation, 1.0)
        self.assertEqual(self.clip.hue, 0.0)

    def test_color_properties_update(self):
        self.clip.brightness = 0.5
        self.clip.contrast = 1.5
        self.clip.saturation = 0.0 # B&W
        self.clip.hue = 90.0
        
        self.assertEqual(self.clip.brightness, 0.5)
        self.assertEqual(self.clip.contrast, 1.5)
        self.assertEqual(self.clip.saturation, 0.0)
        self.assertEqual(self.clip.hue, 90.0)

if __name__ == '__main__':
    unittest.main()
