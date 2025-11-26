import requests
from typing import List, Dict

class StockAPI:
    def __init__(self):
        self.provider = "MockProvider"

    def search_media(self, query: str, media_type: str = "video") -> List[Dict]:
        """
        Search for stock media.
        Returns a list of dicts with keys: id, url, thumbnail, title, duration.
        """
        # Mock implementation for MVP
        print(f"Searching {self.provider} for '{query}' ({media_type})...")
        
        results = []
        for i in range(5):
            results.append({
                "id": f"stock_{i}",
                "title": f"Stock {media_type.capitalize()} {i+1} - {query}",
                "thumbnail": "assets/default_video.png", # Placeholder
                "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", # Sample URL
                "duration": 15.0,
                "provider": self.provider
            })
            
        return results

    def download_media(self, media_id: str, url: str, destination: str):
        """
        Download media file from URL.
        """
        print(f"Downloading {media_id} from {url} to {destination}...")
        # Simulating download
        # In real app: requests.get(url, stream=True) ...
        pass

# Global instance
stock_api = StockAPI()
