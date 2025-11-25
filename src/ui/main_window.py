import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                             QFileDialog, QProgressBar, QMessageBox, QFrame,
                             QListWidget, QStackedWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QSize
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QPixmap, QAction, QDesktopServices
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from src.core.manager import DownloaderManager
import os
import requests
import time

import shutil
import tempfile

# --- Styles ---
DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
    color: #ffffff;
}
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}
/* Sidebar Styles */
QListWidget {
    background-color: #252526;
    border: none;
    outline: none;
    min-width: 200px;
    max-width: 200px;
}
QListWidget::item {
    padding: 15px 20px;
    color: #cccccc;
    border-left: 3px solid transparent;
}
QListWidget::item:selected {
    background-color: #37373d;
    color: #ffffff;
    border-left: 3px solid #007acc;
}
QListWidget::item:hover {
    background-color: #2a2d2e;
}

/* Input Styles */
QLineEdit {
    padding: 12px;
    border: 2px solid #333333;
    border-radius: 8px;
    background-color: #2d2d2d;
    color: #ffffff;
    selection-background-color: #007acc;
}
QLineEdit:focus {
    border: 2px solid #007acc;
}

/* Button Styles */
QPushButton {
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: bold;
    border: none;
}
QPushButton#primary {
    background-color: #007acc;
    color: white;
}
QPushButton#primary:hover {
    background-color: #005c99;
}
QPushButton#secondary {
    background-color: #333333;
    color: white;
}
QPushButton#secondary:hover {
    background-color: #444444;
}

/* Progress Bar */
QProgressBar {
    border: 2px solid #333333;
    border-radius: 5px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #007acc;
}

/* Labels */
QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #007acc;
    margin-bottom: 10px;
}
QLabel#page_title {
    font-size: 28px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 20px;
}

/* Preview Frame */
QFrame#preview_frame {
    border: 2px solid #333333;
    border-radius: 12px;
    background-color: #000000;
}
"""

# --- Worker Threads ---
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
                
        success = self.downloader.download_video(self.url, self.temp_path, self.platform, self.cookies)
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
        
        success = self.downloader.download_video(self.url, self.filename, self.platform, self.cookies)
        self.finished.emit(success, self.filename)

# --- Pages ---

class DownloadPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # State
        self.current_video_url = None
        self.current_platform = None
        self.current_cookies = None
        self.temp_preview_path = None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        title_label = QLabel("Download Video")
        title_label.setObjectName("page_title")
        layout.addWidget(title_label)

        # Input Area
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste TikTok or Douyin link here...")
        self.url_input.returnPressed.connect(self.analyze_url)
        
        self.analyze_btn = QPushButton("Check Video")
        self.analyze_btn.setObjectName("primary")
        self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_btn.clicked.connect(self.analyze_url)
        
        input_layout.addWidget(self.url_input)
        input_layout.addWidget(self.analyze_btn)
        layout.addLayout(input_layout)

        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.status_label)

        # Preview Area
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("preview_frame")
        self.preview_frame.setMinimumHeight(400)
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget()
        preview_layout.addWidget(self.video_widget)
        
        layout.addWidget(self.preview_frame)

        # Initialize downloader
        self.downloader = DownloaderManager()
        
        # Media Player Setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Action Area
        action_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("Save Video")
        self.download_btn.setObjectName("primary")
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.download_video)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        action_layout.addStretch()
        action_layout.addWidget(self.progress_bar)
        action_layout.addWidget(self.download_btn)
        layout.addLayout(action_layout)

    def analyze_url(self):
        text = self.url_input.text().strip()
        if not text:
            return

        # Extract URL from text using regex
        import re
        url_match = re.search(r'https?://[^\s]+', text)
        if url_match:
            url = url_match.group(0)
        else:
            url = text # Fallback to original text if no URL found (though likely invalid)

        self.status_label.setText("Analyzing URL... Please wait.")
        self.analyze_btn.setEnabled(False)
        self.url_input.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.media_player.stop()
        self.temp_preview_path = None

        self.analyzer_thread = AnalyzerThread(url)
        self.analyzer_thread.finished.connect(self.on_analysis_finished)
        self.analyzer_thread.start()

    def on_analysis_finished(self, info):
        if info['status'] == 'success':
            self.status_label.setText(f"Video found! Buffering preview...")
            self.current_video_url = info['url']
            self.current_platform = info['platform']
            self.current_cookies = info.get('cookies')
            
            # Start preview download
            self.preview_thread = PreviewDownloaderThread(self.current_video_url, self.current_platform, self.current_cookies)
            self.preview_thread.finished.connect(self.on_preview_ready)
            self.preview_thread.start()
        else:
            self.reset_ui_state()
            self.status_label.setText(f"Error: {info.get('message', 'Unknown error')}")
            QMessageBox.warning(self, "Error", info.get('message', 'Could not analyze video'))

    def on_preview_ready(self, success, path):
        self.reset_ui_state()
        
        if success:
            self.status_label.setText("Preview ready. Click 'Save Video' to keep it.")
            self.temp_preview_path = path
            self.download_btn.setEnabled(True)
            
            # Play local file
            self.media_player.setSource(QUrl.fromLocalFile(path))
            self.media_player.play()
        else:
            self.status_label.setText("Could not load preview.")
            QMessageBox.warning(self, "Preview Error", "Could not load video preview, but you can try to download it directly.")
            # Enable download anyway in case it works directly
            self.download_btn.setEnabled(True)

    def reset_ui_state(self):
        self.analyze_btn.setEnabled(True)
        self.url_input.setEnabled(True)

    def download_video(self):
        if not self.current_video_url:
            return

        file_filter = "MP4 Video (*.mp4)"
        filename, _ = QFileDialog.getSaveFileName(self, "Save Video", f"video_{self.current_platform}.mp4", file_filter)
        
        if filename:
            self.status_label.setText("Saving...")
            self.download_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0) # Indeterminate
            
            # Pass temp path to use copy instead of re-download if possible
            self.downloader_thread = DownloaderThread(self.current_video_url, filename, self.current_platform, self.temp_preview_path, self.current_cookies)
            self.downloader_thread.finished.connect(self.on_download_finished)
            self.downloader_thread.start()

    def on_download_finished(self, success, filename):
        self.download_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("Saved successfully!")
            QMessageBox.information(self, "Success", f"Video saved to:\n{filename}")
        else:
            self.status_label.setText("Save failed.")
            QMessageBox.critical(self, "Error", "Failed to save video.")

    def cleanup(self):
        # Cleanup temp file
        if self.temp_preview_path and os.path.exists(self.temp_preview_path):
            try:
                os.remove(self.temp_preview_path)
            except:
                pass

class EditPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Edit Video")
        title.setObjectName("page_title")
        layout.addWidget(title)
        
        content = QLabel("Video editing features coming soon...")
        content.setStyleSheet("color: #888888; font-size: 16px;")
        content.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(content)
        layout.addStretch()

class DocumentPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Documents")
        title.setObjectName("page_title")
        layout.addWidget(title)
        
        content = QLabel("Documentation and help files will be here.")
        content.setStyleSheet("color: #888888; font-size: 16px;")
        content.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(content)
        layout.addStretch()

# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Video Downloader")
        self.setMinimumSize(1000, 700)
        
        # Setup UI
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Add items
        self.add_sidebar_item("Edit", "edit")
        self.add_sidebar_item("Download", "download")
        self.add_sidebar_item("Document", "document")
        
        self.sidebar.currentRowChanged.connect(self.change_page)
        main_layout.addWidget(self.sidebar)

        # Content Area
        self.stacked_widget = QStackedWidget()
        
        # Pages
        self.edit_page = EditPage()
        self.download_page = DownloadPage()
        self.document_page = DocumentPage()
        
        self.stacked_widget.addWidget(self.edit_page)
        self.stacked_widget.addWidget(self.download_page)
        self.stacked_widget.addWidget(self.document_page)
        
        main_layout.addWidget(self.stacked_widget)
        
        # Set default page (Download)
        self.sidebar.setCurrentRow(1)

    def add_sidebar_item(self, name, icon_name):
        item = QListWidgetItem(name)
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # Placeholder for icons if we had them
        # item.setIcon(QIcon(f"assets/{icon_name}.png")) 
        self.sidebar.addItem(item)

    def change_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def apply_styles(self):
        self.setStyleSheet(DARK_THEME)

    def closeEvent(self, event):
        # Cleanup pages
        self.download_page.cleanup()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
