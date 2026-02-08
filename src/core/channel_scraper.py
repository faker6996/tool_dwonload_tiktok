"""
TikTok Channel Scraper - Scrape video URLs from a TikTok/Douyin channel.
Uses Playwright for browser automation with session reuse.
"""

import asyncio
import re
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, Browser, Page
from .logging_utils import get_logger

logger = get_logger(__name__)


class ChannelScraper:
    """Scrape video URLs from TikTok/Douyin channels."""
    
    def __init__(self):
        self._browser: Optional[Browser] = None
        self._context = None
        self._playwright = None
    
    async def _ensure_browser(self):
        """Ensure browser is running, reuse if already open."""
        if self._browser is None or not self._browser.is_connected():
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=False,  # Show browser for CAPTCHA
                args=['--disable-blink-features=AutomationControlled']
            )
            self._context = await self._browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800}
            )
        return self._context
    
    async def scrape_channel(
        self,
        channel_url: str,
        max_videos: int = 50,
        days_filter: Optional[int] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[Dict]:
        """
        Scrape video URLs from a TikTok channel.
        
        Args:
            channel_url: URL of the channel (e.g., https://www.tiktok.com/@username)
            max_videos: Maximum number of videos to scrape
            days_filter: Only get videos from last N days (None = all)
            progress_callback: Callback(status_text, count) for progress updates
            
        Returns:
            List of dicts with video info: {url, title, thumbnail, date}
        """
        context = await self._ensure_browser()
        page = await context.new_page()
        
        videos = []
        
        try:
            if progress_callback:
                progress_callback("Opening channel page...", 0)
            
            # Extract URL from text (user may paste share text with extra characters)
            url_match = re.search(r'https?://[^\s]+', channel_url)
            if url_match:
                channel_url = url_match.group(0).rstrip('/')
            
            # Validate URL
            if not channel_url.startswith('http'):
                raise ValueError(f"Invalid URL: {channel_url}")
            
            # Navigate to channel - use domcontentloaded instead of networkidle
            # because Douyin/TikTok pages continuously load content
            await page.goto(channel_url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait a bit for JavaScript to render content
            await asyncio.sleep(3)
            
            # Wait for video grid to load - try different selectors for TikTok vs Douyin
            try:
                await page.wait_for_selector('[data-e2e="user-post-item"]', timeout=15000)
            except:
                # Try Douyin-specific selectors
                try:
                    await page.wait_for_selector('.video-feed-item, .ECMy_qaS, [class*="video-list"]', timeout=15000)
                except:
                    # Just wait and try to scrape anyway
                    await asyncio.sleep(3)
            
            if progress_callback:
                progress_callback("Scanning videos...", 0)
            
            # Calculate cutoff date if filtering
            cutoff_date = None
            if days_filter:
                cutoff_date = datetime.now() - timedelta(days=days_filter)
            
            last_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 20
            
            while len(videos) < max_videos and scroll_attempts < max_scroll_attempts:
                # Get all video items - try TikTok selector first, then Douyin
                video_items = await page.query_selector_all('[data-e2e="user-post-item"]')
                
                # If no TikTok items, try Douyin selectors
                if not video_items:
                    video_items = await page.query_selector_all('.video-feed-item, li[class*="video"], a[href*="/video/"]')
                
                for item in video_items[last_count:]:
                    if len(videos) >= max_videos:
                        break
                    
                    try:
                        # Get video URL
                        link = await item.query_selector('a')
                        if not link:
                            continue
                        
                        href = await link.get_attribute('href')
                        if not href:
                            continue
                        
                        # Make absolute URL
                        if href.startswith('/'):
                            if 'douyin' in channel_url:
                                href = f"https://www.douyin.com{href}"
                            else:
                                href = f"https://www.tiktok.com{href}"
                        
                        # Skip if already added
                        if any(v['url'] == href for v in videos):
                            continue
                        
                        # Try to get thumbnail
                        thumbnail = None
                        img = await item.query_selector('img')
                        if img:
                            thumbnail = await img.get_attribute('src')
                        
                        # Try to get title/description
                        title = ""
                        desc_el = await item.query_selector('[class*="desc"]')
                        if desc_el:
                            title = await desc_el.inner_text()
                        
                        videos.append({
                            'url': href,
                            'title': title[:100] if title else f"Video {len(videos) + 1}",
                            'thumbnail': thumbnail,
                        })
                        
                        if progress_callback:
                            progress_callback(f"Found {len(videos)} videos...", len(videos))
                        
                    except Exception as e:
                        logger.warning("Error parsing video item: %s", e)
                        continue
                
                # Check if we got new videos
                if len(video_items) == last_count:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                    last_count = len(video_items)
                
                # Scroll down to load more
                if len(videos) < max_videos:
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(1.5)  # Wait for content to load
            
            if progress_callback:
                progress_callback(f"Done! Found {len(videos)} videos", len(videos))
            
        except Exception as e:
            logger.warning("Error scraping channel: %s", e)
            if progress_callback:
                progress_callback(f"Error: {str(e)}", len(videos))
        finally:
            await page.close()
        
        return videos
    
    async def close(self):
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    def scrape_channel_sync(
        self,
        channel_url: str,
        max_videos: int = 50,
        days_filter: Optional[int] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[Dict]:
        """Synchronous wrapper for scrape_channel."""
        return asyncio.run(self.scrape_channel(
            channel_url, max_videos, days_filter, progress_callback
        ))


# Global instance for session reuse
channel_scraper = ChannelScraper()
