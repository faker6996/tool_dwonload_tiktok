from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
                             QLabel, QFrame, QProgressBar, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from src.core.manager import DownloaderManager
from ..threads import AnalyzerThread, PreviewDownloaderThread, DownloaderThread
import os

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
