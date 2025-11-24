import pyktok as pyk
import requests
import re
import os
import glob
from playwright.sync_api import sync_playwright

# User Agents
UA_MOBILE = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
UA_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"

class VideoDownloader:
    def __init__(self):
        pass

    def detect_platform(self, url):
        """Detect video platform from URL"""
        url_lower = url.lower()
        if 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'douyin.com' in url_lower:
            return 'douyin'
        else:
            return 'unknown'

    def resolve_short_url(self, url):
        """Resolve short URLs"""
        try:
            response = requests.get(url, headers={"User-Agent": UA_MOBILE}, allow_redirects=True, timeout=10)
            return response.url
        except Exception as e:
            print(f"Failed to resolve: {e}")
            return url

    def extract_video_id(self, url):
        """Extract video ID from URL"""
        patterns = [
            r'/video/(\d+)',           # Standard video URL
            r'/@[^/]+/video/(\d+)',    # User video URL
            r'/t/(\d+)',               # Short URL format
            r'item_id=(\d+)',          # Query parameter
            r'aweme_id=(\d+)',         # Aweme ID
            r'modal_id=(\d+)',         # Douyin modal
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_video_info(self, url):
        """
        Analyze URL and return video information (direct URL, platform, etc.)
        Returns a dictionary: {'status': 'success'/'error', 'url': direct_video_url, 'platform': '...', 'message': '...', 'cookies': {...}}
        """
        # Resolve short URLs
        if any(short in url for short in ['vm.tiktok.com', 'vt.tiktok.com', 'v.douyin.com']):
            url = self.resolve_short_url(url)

        platform = self.detect_platform(url)
        if platform == 'unknown':
            return {'status': 'error', 'message': 'Unsupported platform'}

        video_id = self.extract_video_id(url)
        if not video_id:
            return {'status': 'error', 'message': 'Could not extract video ID'}

        if platform == 'tiktok':
            return self._get_tiktok_video_url(url)

        elif platform == 'douyin':
            return self._get_douyin_video_url(url, video_id)

        return {'status': 'error', 'message': 'Unknown error'}

    def _get_tiktok_video_url(self, url):
        # Use Playwright to intercept network requests
        try:
             with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # TikTok often requires a valid User-Agent
                context = browser.new_context(
                    user_agent=UA_DESKTOP,
                    viewport={'width': 1280, 'height': 720}
                )
                page = context.new_page()
                
                video_urls = []
                
                def handle_response(response):
                    try:
                        # TikTok video URLs usually contain 'video/tos' or similar patterns
                        # and are mp4.
                        if ('video/tos' in response.url or '.mp4' in response.url) and response.status == 200:
                            video_urls.append(response.url)
                    except:
                        pass

                page.on('response', handle_response)
                
                print(f"Navigating to {url}...")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait a bit for the video to start loading
                page.wait_for_timeout(5000)
                
                # Scroll a bit to trigger loading if needed
                page.mouse.wheel(0, 100)
                page.wait_for_timeout(2000)
                
                # Capture cookies
                cookies = context.cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies}
                
                browser.close()
                
                if video_urls:
                    # Filter for the best candidate. 
                    for v_url in video_urls:
                        if '.mp4' in v_url or 'video/tos' in v_url:
                             return {'status': 'success', 'url': v_url, 'platform': 'tiktok', 'cookies': cookie_dict}
                    
                    return {'status': 'success', 'url': video_urls[0], 'platform': 'tiktok', 'cookies': cookie_dict}
                    
        except Exception as e:
            print(f"TikTok extraction error: {e}")
            pass
            
        return {'status': 'error', 'message': 'Could not retrieve TikTok video URL for preview'}

    def _get_douyin_video_url(self, url, video_id):
        # Try API first (missuo.me is good)
        apis = [
            {
                "url": "https://api.missuo.me/douyin",
                "params": {"url": url},
                "key": "mp4"
            },
             {
                "url": "https://api.lolimi.cn/API/douyin/",
                "params": {"url": url},
                "key": "video" # nested in data sometimes, handled below
            }
        ]

        for api in apis:
            try:
                response = requests.get(api["url"], params=api["params"], timeout=10)
                data = response.json()
                if data.get("code") == 200: # missuo
                     video_url = data.get("mp4")
                     if video_url:
                         return {'status': 'success', 'url': video_url, 'platform': 'douyin'}
                # Handle lolimi structure if needed, but let's keep it simple for now
            except:
                continue

        # Fallback to Playwright
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=UA_MOBILE)
                page = context.new_page()
                
                video_urls = []
                page.on('response', lambda response: video_urls.append(response.url) 
                        if ('.mp4' in response.url or '/play/' in response.url) and 'douyin' in response.url else None)
                
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                
                cookies = context.cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies}
                
                browser.close()
                
                if video_urls:
                    # Return the first valid looking one
                    return {'status': 'success', 'url': video_urls[0], 'platform': 'douyin', 'cookies': cookie_dict}
        except Exception as e:
            pass

        return {'status': 'error', 'message': 'Could not retrieve Douyin video URL'}

    def download_video(self, video_url, filename, platform, cookies=None):
        """Download video from direct URL"""
        try:
            headers = {
                "User-Agent": UA_MOBILE,
                "Referer": "https://www.douyin.com/" if platform == 'douyin' else "https://www.tiktok.com/",
            }
            
            response = requests.get(video_url, headers=headers, cookies=cookies, stream=True, timeout=30)
            
            if response.status_code in [200, 206]:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                print(f"Download failed with status: {response.status_code}")
                return False
        except Exception as e:
            print(f"Download error: {e}")
            return False
