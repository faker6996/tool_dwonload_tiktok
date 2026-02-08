import requests
import os
from typing import List, Dict, Optional, Callable
from ..logging_utils import get_logger

logger = get_logger(__name__)

class StockAPI:
    def __init__(self):
        self.provider = "MockProvider"
        self._pexels_api_key = os.getenv("PEXELS_API_KEY", "").strip()
        self._pexels_video_search_url = "https://api.pexels.com/videos/search"

    def search_media(self, query: str, media_type: str = "video") -> List[Dict]:
        """
        Search for stock media.
        Returns a list of dicts with keys: id, url, thumbnail, title, duration.
        """
        active_provider = "Pexels" if self._pexels_api_key else self.provider
        logger.info("Searching %s for '%s' (%s)", active_provider, query, media_type)

        if self._pexels_api_key and media_type == "video":
            try:
                pexels_results = self._search_pexels_videos(query)
                if pexels_results:
                    return pexels_results
                logger.warning("No Pexels results found for '%s', using mock fallback", query)
            except Exception as e:
                logger.warning("Pexels search failed for '%s': %s. Using mock fallback.", query, e)

        return self._search_mock_media(query, media_type)

    def _search_mock_media(self, query: str, media_type: str) -> List[Dict]:
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

    def _search_pexels_videos(self, query: str, per_page: int = 5) -> List[Dict]:
        headers = {"Authorization": self._pexels_api_key}
        params = {
            "query": query,
            "per_page": max(1, min(per_page, 20)),
            "page": 1,
        }
        response = requests.get(
            self._pexels_video_search_url,
            headers=headers,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        videos = payload.get("videos", [])

        results: List[Dict] = []
        for video in videos:
            selected = self._pick_best_video_file(video.get("video_files", []))
            if not selected:
                continue

            video_id = str(video.get("id", "unknown"))
            user_name = (video.get("user") or {}).get("name", "Pexels")
            duration = float(video.get("duration") or 0.0)

            results.append({
                "id": f"pexels_{video_id}",
                "title": f"Pexels {video_id} - {user_name}",
                "thumbnail": video.get("image", ""),
                "url": selected.get("link", ""),
                "duration": duration,
                "provider": "Pexels",
                "width": selected.get("width"),
                "height": selected.get("height"),
            })

        return results[:per_page]

    def _pick_best_video_file(self, video_files: List[Dict]) -> Optional[Dict]:
        if not video_files:
            return None

        mp4_files = [
            f for f in video_files
            if f.get("link") and str(f.get("file_type", "")).lower() in {"video/mp4", "mp4"}
        ]
        candidates = mp4_files or [f for f in video_files if f.get("link")]
        if not candidates:
            return None

        def quality_key(video_file: Dict):
            width = int(video_file.get("width") or 0)
            height = int(video_file.get("height") or 0)
            pixel_count = width * height
            return (abs(width - 720), pixel_count)

        candidates.sort(key=quality_key)
        return candidates[0]

    def download_media(
        self,
        media_id: str,
        url: str,
        destination: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        should_abort: Optional[Callable[[], bool]] = None,
    ) -> str:
        """
        Download media file from URL.
        """
        logger.info("Downloading %s from %s to %s", media_id, url, destination)

        destination_dir = os.path.dirname(destination)
        if destination_dir:
            os.makedirs(destination_dir, exist_ok=True)

        temp_destination = f"{destination}.part"
        try:
            with requests.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()
                total_bytes = int((response.headers or {}).get("Content-Length", 0) or 0)
                bytes_written = 0
                if progress_callback:
                    progress_callback(0, total_bytes)

                with open(temp_destination, "wb") as output_file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if should_abort and should_abort():
                            raise RuntimeError("Download cancelled")
                        if chunk:
                            output_file.write(chunk)
                            bytes_written += len(chunk)
                            if progress_callback:
                                progress_callback(bytes_written, total_bytes)

                if progress_callback:
                    progress_callback(bytes_written, total_bytes)

            os.replace(temp_destination, destination)
            return destination
        except Exception as e:
            logger.warning("Stock media download failed for %s: %s", media_id, e)
            if os.path.exists(temp_destination):
                try:
                    os.remove(temp_destination)
                except OSError:
                    pass
            return ""

# Global instance
stock_api = StockAPI()
