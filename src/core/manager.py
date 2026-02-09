import re
import time
from urllib.parse import parse_qs, urlparse
from .platforms.tiktok import TikTokDownloader
from .platforms.douyin import DouyinDownloader
from .platforms.generic import GenericDownloader
from .logging_utils import get_logger

logger = get_logger(__name__)

class DownloaderManager:
    def __init__(self):
        self.tiktok_downloader = TikTokDownloader()
        self.douyin_downloader = DouyinDownloader()
        self.generic_downloader = GenericDownloader()
        
        # Specific instances for other platforms using GenericDownloader logic
        self.youtube_downloader = GenericDownloader("youtube")
        self.facebook_downloader = GenericDownloader("facebook")
        self.instagram_downloader = GenericDownloader("instagram")
        self.twitter_downloader = GenericDownloader("twitter")

    def detect_platform(self, url):
        url = url.lower()
        if 'tiktok.com' in url:
            return 'tiktok'
        elif 'douyin.com' in url or 'iesdouyin.com' in url:
            return 'douyin'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'facebook.com' in url or 'fb.watch' in url:
            return 'facebook'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'twitter'
        elif 'threads.net' in url:
            return 'threads'
        return 'unknown'

    def get_downloader(self, platform):
        if platform == 'tiktok':
            return self.tiktok_downloader
        elif platform == 'douyin':
            return self.douyin_downloader
        elif platform == 'youtube':
            return self.youtube_downloader
        elif platform == 'facebook':
            return self.facebook_downloader
        elif platform == 'instagram':
            return self.instagram_downloader
        elif platform == 'twitter':
            return self.twitter_downloader
        else:
            return self.generic_downloader

    def resolve_short_url(self, url):
        import requests
        try:
            # Simple check for short domains
            if any(short in url for short in ['vm.tiktok.com', 'vt.tiktok.com', 'v.douyin.com', 'fb.watch', 'bit.ly', 'goo.gl']):
                logger.info("Resolving short URL: %s", url)
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=10)
                logger.info("Resolved short URL to: %s", response.url)
                return response.url
        except Exception as e:
            logger.warning("Failed to resolve short URL: %s", e)
        return url

    def normalize_youtube_url(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            path = parsed.path or ""

            if "youtu.be" in host:
                video_id = path.strip("/").split("/")[0]
                if video_id:
                    return f"https://www.youtube.com/watch?v={video_id}"

            if "youtube.com" in host or "youtube-nocookie.com" in host:
                if path.startswith("/shorts/"):
                    video_id = path.split("/shorts/")[-1].split("/")[0]
                    if video_id:
                        return f"https://www.youtube.com/watch?v={video_id}"
                if path == "/watch":
                    query = parse_qs(parsed.query or "")
                    video_id = (query.get("v") or [None])[0]
                    if video_id:
                        return f"https://www.youtube.com/watch?v={video_id}"
        except Exception:
            pass
        return url

    def _notify_status(self, status_callback, message: str):
        if not status_callback:
            return
        try:
            status_callback(message)
        except Exception:
            pass

    def get_video_info(self, url, status_callback=None):
        started_at = time.monotonic()

        self._notify_status(status_callback, "Resolving URL...")
        # Resolve short URLs
        url = self.resolve_short_url(url)
        url = self.normalize_youtube_url(url)

        self._notify_status(status_callback, "Detecting platform...")
        platform = self.detect_platform(url)
        downloader = self.get_downloader(platform)

        logger.info("Detected platform: %s", platform)
        self._notify_status(status_callback, f"Fetching metadata from {platform}...")
        info = downloader.extract_info(url, status_callback=status_callback)

        elapsed = time.monotonic() - started_at
        if isinstance(info, dict) and info.get("status") == "success":
            info.setdefault("source_url", url)
            info.setdefault("analysis_seconds", elapsed)
            self._notify_status(status_callback, f"Done in {elapsed:.1f}s")
            return info

        if isinstance(info, dict):
            info.setdefault("analysis_seconds", elapsed)

        self._notify_status(status_callback, f"Failed after {elapsed:.1f}s")
        return info

    def download_video(
        self,
        video_url,
        filename,
        platform,
        cookies=None,
        user_agent=None,
        progress_callback=None,
    ):
        downloader = self.get_downloader(platform)
        if progress_callback is None:
            return downloader.download(video_url, filename, cookies, user_agent)
        return downloader.download(
            video_url,
            filename,
            cookies,
            user_agent,
            progress_callback=progress_callback,
        )

    def download_audio(
        self,
        source_url,
        filename,
        platform,
        cookies=None,
        user_agent=None,
        progress_callback=None,
    ):
        downloader = self.get_downloader(platform)
        if hasattr(downloader, "download_audio"):
            if progress_callback is None:
                return downloader.download_audio(source_url, filename, cookies, user_agent)
            return downloader.download_audio(
                source_url,
                filename,
                cookies,
                user_agent,
                progress_callback=progress_callback,
            )
        logger.warning("Downloader for platform %s does not support audio mode", platform)
        return False
