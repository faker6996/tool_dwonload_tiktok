from ..base import BaseDownloader
from playwright.sync_api import sync_playwright
import requests

UA_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"

class DouyinDownloader(BaseDownloader):
    def extract_info(self, url):
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
        captured_cookies = []
        captured_cookie_dict = {}
        
        try:
            with sync_playwright() as p:
                print("Launching browser for manual interaction...")
                browser = p.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context = browser.new_context(
                    user_agent=UA_DESKTOP,
                    viewport={'width': 1280, 'height': 720},
                    locale='en-US'
                )
                
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                page = context.new_page()
                
                # Shared state for the closure
                state = {'found_url': None}

                def handle_response(response):
                    try:
                        r_url = response.url
                        # Check for video content types or mp4 extension
                        content_type = response.headers.get('content-type', '').lower()
                        if 'video/' in content_type or '.mp4' in r_url:
                            # Check size if available
                            try:
                                length = int(response.headers.get('content-length', 0))
                            except:
                                length = 0
                                
                            if length > 500 * 1024: # > 500KB
                                print(f"Found potential video: {r_url} (Size: {length})")
                                if not state['found_url']:
                                    state['found_url'] = r_url
                    except Exception as e:
                        pass

                page.on('response', handle_response)
                
                print(f"Navigating to Douyin: {url}")
                print("Please solve any captcha if it appears in the browser window.")
                
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                except:
                    print("Navigation timeout, but continuing to check for video...")

                # Wait loop (up to 120 seconds for manual interaction)
                for i in range(60):
                    if state['found_url']:
                        print("Successfully captured video URL!")
                        # Capture cookies at this moment
                        captured_cookies = context.cookies()
                        captured_cookie_dict = {c['name']: c['value'] for c in captured_cookies}
                        break
                    
                    if i % 5 == 0:
                        print(f"Waiting for video... ({i*2}s)")
                    
                    page.wait_for_timeout(2000)
                    # Scroll to trigger loading
                    page.mouse.wheel(0, 100)

                browser.close()
                
                if state['found_url']:
                    return {'status': 'success', 'url': state['found_url'], 'platform': 'douyin', 'cookies': captured_cookie_dict}
                            
        except Exception as e:
            print(f"Playwright error: {e}")
            pass

        # Return error but include cookies if we got them
        return {'status': 'error', 'message': 'Could not retrieve Douyin video URL', 'cookies': captured_cookie_dict, 'playwright_cookies': captured_cookies, 'user_agent': UA_DESKTOP}
