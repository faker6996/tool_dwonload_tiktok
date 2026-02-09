from ..base import BaseDownloader
from playwright.sync_api import sync_playwright
import re
from ..logging_utils import get_logger

logger = get_logger(__name__)

UA_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"

class TikTokDownloader(BaseDownloader):
    def extract_info(self, url, status_callback=None):
        def _notify(message: str):
            if not status_callback:
                return
            try:
                status_callback(message)
            except Exception:
                pass

        # Use Playwright to intercept network requests
        try:
             _notify("Launching browser engine...")
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
                
                logger.info("Navigating to %s", url)
                _notify("Opening TikTok page...")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait a bit for the video to start loading
                _notify("Scanning network requests for video stream...")
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
                             _notify("Video stream found")
                             return {'status': 'success', 'url': v_url, 'platform': 'tiktok', 'cookies': cookie_dict}
                    
                    _notify("Video stream found")
                    return {'status': 'success', 'url': video_urls[0], 'platform': 'tiktok', 'cookies': cookie_dict}
                    
        except Exception as e:
            logger.warning("TikTok extraction error: %s", e)
            pass
            
        return {'status': 'error', 'message': 'Could not retrieve TikTok video URL for preview'}
