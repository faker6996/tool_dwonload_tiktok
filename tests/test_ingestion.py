import unittest
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.ingestion import MediaIngestion

class TestIngestion(unittest.TestCase):
    def setUp(self):
        self.ingestion = MediaIngestion()
        
    def test_probe_non_existent_file(self):
        result = self.ingestion.probe_file("non_existent.mp4")
        self.assertIsNone(result)

    # We can't easily test a real file without having one. 
    # But we can check if the class instantiates and methods exist.

if __name__ == '__main__':
    unittest.main()
