import unittest
import sys
import os
import shutil
import tempfile
import time
from PyQt6.QtCore import QCoreApplication

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.export.renderer import render_engine

class TestExport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Create a QCoreApplication if not exists (needed for signals)
        if not QCoreApplication.instance():
            self.app = QCoreApplication(sys.argv)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_render_engine_handles_empty_timeline(self):
        output_path = os.path.join(self.temp_dir, "output.mp4")
        settings = {"resolution": "1920x1080", "fps": 30}
        
        # Track signals
        self.progress_values = []
        self.finished = False
        self.success = None
        self.message = ""
        
        def on_progress(val):
            self.progress_values.append(val)
            
        def on_finished(success, msg):
            self.finished = True
            self.success = success
            self.message = msg
            
        render_engine.progress_updated.connect(on_progress)
        render_engine.render_finished.connect(on_finished)
        
        # Start Render
        render_engine.render_timeline([], output_path, settings)
        
        # Wait for completion (Mock takes ~5s: 100 steps * 0.05s)
        # We'll wait a bit more
        start_time = time.time()
        while not self.finished and time.time() - start_time < 10:
            QCoreApplication.processEvents()
            time.sleep(0.1)
            
        self.assertTrue(self.finished)
        self.assertFalse(self.success)
        self.assertEqual(self.message, "No clips to render.")
        self.assertEqual(self.progress_values, [])
        self.assertFalse(os.path.exists(output_path))

if __name__ == '__main__':
    unittest.main()
