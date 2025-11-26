import unittest
import sys
import os
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.timeline.clip import Clip
from src.ui.panels.inspector import Inspector

# Create app instance for widgets
app = QApplication(sys.argv)

class TestInspectorIntegration(unittest.TestCase):
    def setUp(self):
        self.inspector = Inspector()
        self.clip = Clip("c1", "Test Clip", duration=5.0)
        self.clip.position_x = 100.0
        self.clip.scale_x = 1.5

    def test_set_clip_updates_ui(self):
        # Set clip
        self.inspector.set_clip(self.clip)
        
        # Verify UI values match clip data
        self.assertEqual(self.inspector.pos_x.value(), 100.0)
        self.assertEqual(self.inspector.scale_x.value(), 1.5)
        self.assertTrue(self.inspector.content_widget.isEnabled())

    def test_ui_change_updates_clip(self):
        self.inspector.set_clip(self.clip)
        
        # Simulate UI change
        self.inspector.pos_x.setValue(200.0)
        
        # Verify clip data updated
        self.assertEqual(self.clip.position_x, 200.0)

    def test_deselect_clip(self):
        self.inspector.set_clip(None)
        self.assertFalse(self.inspector.content_widget.isEnabled())

if __name__ == '__main__':
    unittest.main()
