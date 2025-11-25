import re
from .platforms.tiktok import TikTokDownloader
from .platforms.douyin import DouyinDownloader
from .platforms.generic import GenericDownloader

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
                print(f"Resolving short URL: {url}")
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=10)
                print(f"Resolved to: {response.url}")
                return response.url
        except Exception as e:
            print(f"Failed to resolve: {e}")
        return url

    def get_video_info(self, url):
        # Resolve short URLs
        url = self.resolve_short_url(url)
        
        platform = self.detect_platform(url)
        downloader = self.get_downloader(platform)
        
        print(f"Detected platform: {platform}")
        return downloader.extract_info(url)

    def download_video(self, video_url, filename, platform, cookies=None, user_agent=None):
        downloader = self.get_downloader(platform)
        return downloader.download(video_url, filename, cookies, user_agent)
