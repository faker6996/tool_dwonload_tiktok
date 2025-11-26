import unittest
import sys
import os
import shutil
import tempfile
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.api.stock_api import stock_api
from src.ui.panels.media_pool import MediaPool

# Create App instance for UI tests
app = QApplication(sys.argv)

class TestAssetManagement(unittest.TestCase):
    def test_stock_api_search(self):
        results = stock_api.search_media("nature")
        self.assertEqual(len(results), 5)
        self.assertIn("nature", results[0]["title"].lower())
        self.assertEqual(results[0]["provider"], "MockProvider")

    def test_media_pool_filter(self):
        # This is a UI test, harder to test without full state. 
        # But we can verify the method exists and runs without error.
        pool = MediaPool()
        pool.search_input.setText("test")
        pool.filter_assets() # Should run without error
        
        # Test Stock Search UI trigger
        pool.stock_search_input.setText("test")
        pool.search_stock()
        self.assertEqual(pool.stock_list.count(), 5)

if __name__ == '__main__':
    unittest.main()
