from PyQt6.QtCore import QThread, pyqtSignal
from src.core.manager import DownloaderManager
import os
import tempfile

class AnalyzerThread(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.downloader = DownloaderManager()

    def run(self):
        def _emit_progress(message: str):
            if message:
                self.progress.emit(str(message))

        info = self.downloader.get_video_info(self.url, status_callback=_emit_progress)
        self.finished.emit(info)

class PreviewDownloaderThread(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, url, platform, cookies=None):
        super().__init__()
        self.url = url
        self.platform = platform
        self.cookies = cookies
        self.downloader = DownloaderManager()
        self.temp_path = os.path.join(tempfile.gettempdir(), 'preview_video.mp4')

    def run(self):
        # Remove existing temp file
        if os.path.exists(self.temp_path):
            try:
                os.remove(self.temp_path)
            except:
                pass
                
        result = self.downloader.download_video(self.url, self.temp_path, self.platform, self.cookies)
        
        # Handle both dict and bool return types
        if isinstance(result, dict):
            success = result.get('status') == 'success'
        else:
            success = bool(result)
            
        self.finished.emit(success, self.temp_path)

class DownloaderThread(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(object, object)
    
    def __init__(
        self,
        url,
        filename,
        platform,
        source_path=None,
        cookies=None,
        download_mode="video",
        source_url=None,
    ):
        super().__init__()
        self.url = url
        self.filename = filename
        self.platform = platform
        self.source_path = source_path
        self.cookies = cookies
        self.download_mode = download_mode
        self.source_url = source_url
        self.downloader = DownloaderManager()

    def _emit_progress(self, downloaded, total):
        try:
            downloaded_value = int(downloaded or 0)
        except Exception:
            downloaded_value = 0
        try:
            total_value = int(total or 0)
        except Exception:
            total_value = 0
        self.progress.emit(downloaded_value, total_value)

    def _copy_with_progress(self, source_path: str, destination_path: str) -> bool:
        total_size = 0
        try:
            total_size = os.path.getsize(source_path)
        except OSError:
            total_size = 0

        copied = 0
        chunk_size = 1024 * 1024
        os.makedirs(os.path.dirname(os.path.abspath(destination_path)) or ".", exist_ok=True)

        with open(source_path, "rb") as src, open(destination_path, "wb") as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                copied += len(chunk)
                self._emit_progress(copied, total_size)
        self._emit_progress(total_size or copied, total_size or copied)
        return True

    def run(self):
        self._emit_progress(0, 0)
        if self.download_mode == "audio":
            source_url = self.source_url or self.url
            result = self.downloader.download_audio(
                source_url,
                self.filename,
                self.platform,
                self.cookies,
                progress_callback=self._emit_progress,
            )
            success = bool(result)
            self.finished.emit(success, self.filename)
            return

        if self.source_path and os.path.exists(self.source_path):
            # Copy from temp file if available
            try:
                self._copy_with_progress(self.source_path, self.filename)
                self.finished.emit(True, self.filename)
                return
            except Exception as e:
                print(f"Copy failed: {e}")
                # Fallback to download

        download_url = self.url
        if self.platform == "youtube" and self.source_url:
            download_url = self.source_url

        result = self.downloader.download_video(
            download_url,
            self.filename,
            self.platform,
            self.cookies,
            progress_callback=self._emit_progress,
        )
        
        # Handle both dict and bool return types
        if isinstance(result, dict):
            success = result.get('status') == 'success'
        else:
            success = bool(result)
            
        self.finished.emit(success, self.filename)

class IngestionThread(QThread):
    asset_processed = pyqtSignal(dict)
    finished = pyqtSignal()
    
    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths
        from src.core.ingestion import MediaIngestion
        self.ingestion = MediaIngestion()

    def run(self):
        for file_path in self.file_paths:
            asset = self.ingestion.probe_file(file_path)
            if asset:
                self.asset_processed.emit(asset)
        self.finished.emit()


class StockDownloadThread(QThread):
    """Download stock media in background to avoid blocking UI."""

    progress = pyqtSignal(int)  # percent (0-100)
    finished = pyqtSignal(bool, str, dict)  # success, file_path, stock_item

    def __init__(self, stock_item: dict, destination_path: str):
        super().__init__()
        self.stock_item = stock_item
        self.destination_path = destination_path
        self._cancel_requested = False

    @property
    def cancel_requested(self) -> bool:
        return self._cancel_requested

    def cancel(self):
        self._cancel_requested = True

    def run(self):
        try:
            from src.core.api.stock_api import stock_api

            media_id = str(self.stock_item.get("id", "stock_item"))
            url = str(self.stock_item.get("url", "")).strip()
            if not url or self._cancel_requested:
                self.finished.emit(False, "", self.stock_item)
                return

            def _on_progress(downloaded: int, total: int):
                if total > 0:
                    percent = int(max(0, min(100, (downloaded * 100) / total)))
                    self.progress.emit(percent)

            self.progress.emit(0)
            saved_path = stock_api.download_media(
                media_id,
                url,
                self.destination_path,
                progress_callback=_on_progress,
                should_abort=lambda: self._cancel_requested,
            )
            success = bool(saved_path and os.path.exists(saved_path) and not self._cancel_requested)
            if success:
                self.progress.emit(100)
            self.finished.emit(success, saved_path or "", self.stock_item)
        except Exception:
            self.finished.emit(False, "", self.stock_item)


class ChannelScraperThread(QThread):
    """Thread for scraping channel videos in background."""
    
    progress = pyqtSignal(str, int)  # status_text, count
    finished = pyqtSignal(list)  # list of video dicts
    error = pyqtSignal(str)
    
    def __init__(self, channel_url: str, max_videos: int = 50, days_filter: int = None):
        super().__init__()
        self.channel_url = channel_url
        self.max_videos = max_videos
        self.days_filter = days_filter
    
    def run(self):
        try:
            import asyncio
            from src.core.channel_scraper import channel_scraper
            
            def progress_callback(status: str, count: int):
                self.progress.emit(status, count)
            
            # Run async scraper in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                videos = loop.run_until_complete(
                    channel_scraper.scrape_channel(
                        self.channel_url,
                        self.max_videos,
                        self.days_filter,
                        progress_callback
                    )
                )
                self.finished.emit(videos)
            finally:
                loop.close()
                
        except Exception as e:
            self.error.emit(str(e))
