from ..base import BaseDownloader
import yt_dlp
import tempfile
import os
import requests

UA_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class DouyinDownloader(BaseDownloader):
    def __init__(self):
        self.cookies_from_browser = 'chrome'
        
    def extract_info(self, url):
        """Extract video info - try yt-dlp first, then Playwright."""
        print(f"Extracting Douyin video: {url}")
        
        # Try yt-dlp with browser cookies first
        result = self._try_ytdlp(url)
        if result.get('status') == 'success':
            return result
        
        # Fallback to Playwright (opens browser for manual interaction)
        print("yt-dlp failed, trying Playwright browser capture...")
        return self._try_playwright(url)
    
    def _try_ytdlp(self, url):
        """Try downloading with yt-dlp and browser cookies."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'user_agent': UA_DESKTOP,
        }
        
        for browser in ['chrome', 'firefox', 'safari']:
            try:
                ydl_opts['cookiesfrombrowser'] = (browser,)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        formats = info.get('formats', [])
                        video_url = None
                        for fmt in reversed(formats):
                            if fmt.get('ext') == 'mp4' and fmt.get('url'):
                                video_url = fmt['url']
                                break
                        if not video_url and info.get('url'):
                            video_url = info['url']
                        if video_url:
                            return {
                                'status': 'success',
                                'url': video_url,
                                'platform': 'douyin',
                                'title': info.get('title', 'Douyin Video'),
                            }
            except:
                continue
        
        return {'status': 'error', 'message': 'yt-dlp failed'}
    
    def _try_playwright(self, url):
        """Open browser for manual interaction and capture video URL."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return {
                'status': 'error',
                'message': 'Playwright not installed. Run: pip install playwright && playwright install'
            }
        
        state = {'video_url': None, 'title': None}
        
        try:
            with sync_playwright() as p:
                print("\n" + "="*50)
                print("🌐 Mở browser để tải video Douyin...")
                print("📌 Nếu cần đăng nhập hoặc giải captcha, vui lòng thao tác")
                print("="*50 + "\n")
                
                browser = p.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context = browser.new_context(
                    user_agent=UA_DESKTOP,
                    viewport={'width': 1280, 'height': 720},
                    locale='zh-CN'
                )
                
                # Anti-detection
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    window.chrome = { runtime: {} };
                """)
                
                page = context.new_page()
                
                # Intercept video responses
                def handle_response(response):
                    try:
                        r_url = response.url
                        content_type = response.headers.get('content-type', '').lower()
                        
                        # Check for video content
                        if ('video/' in content_type or 
                            '.mp4' in r_url or 
                            'aweme/v1/play' in r_url or
                            'video/tos' in r_url):
                            
                            try:
                                length = int(response.headers.get('content-length', 0))
                            except:
                                length = 0
                            
                            # Videos are usually > 500KB
                            if length > 500 * 1024 or 'aweme/v1/play' in r_url:
                                if not state['video_url']:
                                    print(f"✅ Found video URL! (Size: {length/1024:.0f}KB)")
                                    state['video_url'] = r_url
                    except:
                        pass

                page.on('response', handle_response)
                
                print(f"Navigating to: {url}")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                except:
                    print("Navigation timeout, waiting for video...")
                
                # Try to get title - use more specific selectors for Douyin
                try:
                    # Wait a bit for page to load
                    page.wait_for_timeout(1000)
                    
                    # Try multiple selectors in order of specificity
                    title_selectors = [
                        '[data-e2e="video-desc"]',  # Video description
                        '.video-info-detail .title',
                        '.video-info-title',
                        'span[class*="title"]',
                        '.xgplayer-title',
                        'meta[property="og:title"]',
                        'meta[name="description"]',
                    ]
                    
                    for selector in title_selectors:
                        try:
                            if selector.startswith('meta'):
                                el = page.query_selector(selector)
                                if el:
                                    content = el.get_attribute('content')
                                    if content and len(content) > 5:
                                        state['title'] = content[:200]
                                        print(f"📝 Found title: {state['title'][:50]}...")
                                        break
                            else:
                                el = page.query_selector(selector)
                                if el:
                                    text = el.inner_text().strip()
                                    # Skip if too short or looks like UI element
                                    if text and len(text) > 5 and '搜索' not in text and 'search' not in text.lower():
                                        state['title'] = text[:200]
                                        print(f"📝 Found title: {state['title'][:50]}...")
                                        break
                        except:
                            continue
                except Exception as e:
                    print(f"⚠️ Could not extract title: {e}")
                
                # Wait for video to load (up to 60 seconds)
                print("\n⏳ Đang chờ video load...")
                print("💡 Nếu cần đăng nhập/giải captcha, vui lòng thao tác trong browser\n")
                
                for i in range(30):
                    if state['video_url']:
                        print("✅ Đã capture video URL thành công!")
                        break
                    
                    if i % 5 == 0:
                        print(f"   Waiting... ({i*2}s)")
                    
                    page.wait_for_timeout(2000)
                    
                    # Auto scroll to trigger video loading
                    try:
                        page.mouse.wheel(0, 100)
                        page.keyboard.press("Space")  # Try to play video
                    except:
                        pass
                
                browser.close()
                
                if state['video_url']:
                    return {
                        'status': 'success',
                        'url': state['video_url'],
                        'platform': 'douyin',
                        'title': state.get('title') or 'Douyin Video',
                        'method': 'playwright'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'Không tìm thấy video URL. Vui lòng thử lại hoặc đăng nhập trong browser.'
                    }
                    
        except Exception as e:
            print(f"Playwright error: {e}")
            return {
                'status': 'error',
                'message': f'Browser error: {str(e)}'
            }
    
    def download(self, url, output_path, cookies=None, user_agent=None):
        """Download video to file."""
        info = self.extract_info(url)
        
        if info.get('status') != 'success':
            return info
        
        video_url = info.get('url')
        if not video_url:
            return {'status': 'error', 'message': 'No video URL found'}
        
        print(f"Downloading from: {video_url[:80]}...")
        
        try:
            headers = {
                'User-Agent': user_agent or UA_DESKTOP,
                'Referer': 'https://www.douyin.com/',
            }
            
            response = requests.get(video_url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
                return {
                    'status': 'success',
                    'path': output_path,
                    'title': info.get('title', 'Douyin Video')
                }
            else:
                return {'status': 'error', 'message': 'Downloaded file too small'}
                
        except Exception as e:
            return {'status': 'error', 'message': f'Download failed: {str(e)}'}
