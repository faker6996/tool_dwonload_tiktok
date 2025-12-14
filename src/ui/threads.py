from PyQt6.QtCore import QThread, pyqtSignal
from src.core.manager import DownloaderManager
import os
import tempfile
import shutil

class AnalyzerThread(QThread):
    finished = pyqtSignal(dict)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.downloader = DownloaderManager()

    def run(self):
        info = self.downloader.get_video_info(self.url)
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
    
    def __init__(self, url, filename, platform, source_path=None, cookies=None):
        super().__init__()
        self.url = url
        self.filename = filename
        self.platform = platform
        self.source_path = source_path
        self.cookies = cookies
        self.downloader = DownloaderManager()

    def run(self):
        if self.source_path and os.path.exists(self.source_path):
            # Copy from temp file if available
            try:
                shutil.copy2(self.source_path, self.filename)
                self.finished.emit(True, self.filename)
                return
            except Exception as e:
                print(f"Copy failed: {e}")
                # Fallback to download
        
        result = self.downloader.download_video(self.url, self.filename, self.platform, self.cookies)
        
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
