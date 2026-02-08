import os
import sys
import unittest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.state import state_manager


class TestStateManager(unittest.TestCase):
    def setUp(self):
        self.assets_backup = dict(state_manager.state["media_pool"]["assets"])
        state_manager.state["media_pool"]["assets"] = {}

    def tearDown(self):
        state_manager.state["media_pool"]["assets"] = self.assets_backup

    def test_find_asset_by_path(self):
        asset = {
            "id": "asset-1",
            "target_url": "/tmp/video.mp4",
            "metadata": {"duration": 5.0},
        }
        state_manager.add_asset(asset)

        found = state_manager.find_asset_by_path("/tmp/video.mp4")
        self.assertIsNotNone(found)
        self.assertEqual(found["id"], "asset-1")

    def test_find_asset_by_path_returns_none_when_missing(self):
        found = state_manager.find_asset_by_path("/tmp/missing.mp4")
        self.assertIsNone(found)


if __name__ == "__main__":
    unittest.main()
