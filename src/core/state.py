from typing import Dict, List, Any
from PyQt6.QtCore import QObject, pyqtSignal

class StateManager(QObject):
    """
    Singleton-like State Manager for the application.
    Uses PyQt signals to notify UI of state changes.
    """
    _instance = None
    
    # Signals
    media_imported = pyqtSignal(dict) # Emits the new asset object
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        
        # Initial State
        self.state = {
            "project": {
                "name": "Untitled Project",
                "resolution": (1920, 1080),
                "fps": 30.0
            },
            "media_pool": {
                "assets": {} # Dict[uuid, Asset]
            }
        }

    def add_asset(self, asset: Dict):
        """
        Add an asset to the media pool and notify listeners.
        """
        asset_id = asset["id"]
        self.state["media_pool"]["assets"][asset_id] = asset
        self.media_imported.emit(asset)

    def get_assets(self) -> List[Dict]:
        return list(self.state["media_pool"]["assets"].values())

    def get_asset(self, asset_id: str) -> Dict:
        return self.state["media_pool"]["assets"].get(asset_id)

# Global instance
state_manager = StateManager()
