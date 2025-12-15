from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
                             QLabel, QFrame, QProgressBar, QFileDialog, QMessageBox,
                             QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QUrl, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QMovie, QPainter, QColor, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from src.core.manager import DownloaderManager
from ..threads import AnalyzerThread, PreviewDownloaderThread, DownloaderThread
import os


class LoadingOverlay(QWidget):
    """Semi-transparent overlay with loading spinner and status text."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Spinner (animated dots)
        self.spinner_label = QLabel()
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinner_label.setStyleSheet("font-size: 48px; color: #3498db;")
        layout.addWidget(self.spinner_label)
        
        # Status text
        self.status_label = QLabel("Loading...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 16px; 
            color: #ffffff; 
            background: rgba(0, 0, 0, 0.7);
            padding: 10px 20px;
            border-radius: 8px;
        """)
        layout.addWidget(self.status_label)
        
        # Animation timer for spinner
        self.spinner_frame = 0
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self._update_spinner)
        
    def showEvent(self, event):
        super().showEvent(event)
        self.spinner_timer.start(150)  # Update every 150ms
        self._resize_to_parent()
        
    def hideEvent(self, event):
        super().hideEvent(event)
        self.spinner_timer.stop()
        
    def _resize_to_parent(self):
        if self.parent():
            self.setGeometry(self.parent().rect())
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_to_parent()
        
    def _update_spinner(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_frame = (self.spinner_frame + 1) % len(frames)
        self.spinner_label.setText(frames[self.spinner_frame])
        
    def set_text(self, text: str):
        self.status_label.setText(text)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))  # Semi-transparent black

class DownloadPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # State
        self.current_video_url = None
        self.current_platform = None
        self.current_cookies = None
        self.temp_preview_path = None
        self.video_title = None  # Store video title for auto-naming

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
        
        # Video Controls
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        self.play_pause_btn = QPushButton("▶ Play")
        self.play_pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_pause_btn.setFixedWidth(100)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.play_pause_btn.setEnabled(False)
        controls_layout.addWidget(self.play_pause_btn)
        
        controls_layout.addStretch()
        preview_layout.addLayout(controls_layout)
        
        layout.addWidget(self.preview_frame)
        
        # Loading overlay (must be created after preview_frame)
        self.loading_overlay = LoadingOverlay(self.preview_frame)
        self.loading_overlay.hide()

        # Initialize downloader
        self.downloader = DownloaderManager()
        
        # Media Player Setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.media_player.bufferProgressChanged.connect(self.on_buffer_progress)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)

        # Action Area
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumWidth(200)
        
        self.download_btn = QPushButton("Save Video")
        self.download_btn.setObjectName("primary")
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setEnabled(False)
        self.download_btn.setMinimumWidth(120)
        self.download_btn.clicked.connect(self.download_video)
        
        action_layout.addWidget(self.progress_bar)
        action_layout.addStretch()
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
        
        # Show loading overlay
        self.loading_overlay.set_text("🔍 Analyzing URL...")
        self.loading_overlay.show()

        self.analyzer_thread = AnalyzerThread(url)
        self.analyzer_thread.finished.connect(self.on_analysis_finished)
        self.analyzer_thread.start()

    def on_analysis_finished(self, info):
        if info['status'] == 'success':
            self.status_label.setText(f"Video found! Downloading preview...")
            self.current_video_url = info['url']
            self.current_platform = info['platform']
            self.current_cookies = info.get('cookies')
            self.video_title = info.get('title', '')  # Store title for filename
            
            # Update loading overlay
            self.loading_overlay.set_text("📥 Downloading preview...")
            
            # Start preview download
            self.preview_thread = PreviewDownloaderThread(self.current_video_url, self.current_platform, self.current_cookies)
            self.preview_thread.finished.connect(self.on_preview_ready)
            self.preview_thread.start()
        else:
            self.loading_overlay.hide()
            self.reset_ui_state()
            self.status_label.setText(f"Error: {info.get('message', 'Unknown error')}")
            QMessageBox.warning(self, "Error", info.get('message', 'Could not analyze video'))

    def on_preview_ready(self, success, path):
        self.reset_ui_state()
        
        if success:
            self.status_label.setText("Preview ready. Click 'Save Video' to keep it.")
            self.temp_preview_path = path
            self.download_btn.setEnabled(True)
            self.play_pause_btn.setEnabled(True)
            
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

        # Auto-generate filename from video title
        import re
        import time
        
        if self.video_title:
            # Translate title to Vietnamese
            translated_title = self._translate_title_to_vietnamese(self.video_title)
            
            # Sanitize title: remove special chars, keep Vietnamese/Chinese chars, limit length
            safe_title = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF\u4e00-\u9fff-]', '', translated_title)
            safe_title = safe_title.strip()[:80]  # Limit to 80 chars (Vietnamese can be longer)
            if not safe_title:
                safe_title = f"video_{self.current_platform}"
        else:
            safe_title = f"video_{self.current_platform}_{int(time.time())}"
        
        default_filename = f"{safe_title}.mp4"

        file_filter = "MP4 Video (*.mp4)"
        filename, _ = QFileDialog.getSaveFileName(self, "Save Video", default_filename, file_filter)
        
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
        
        # Auto-pause video on download complete
        self.media_player.pause()
        
        if success:
            self.status_label.setText("Saved successfully!")
            QMessageBox.information(self, "Success", f"Video saved to:\n{filename}")
        else:
            self.status_label.setText("Save failed.")
            QMessageBox.critical(self, "Error", "Failed to save video.")
    
    def toggle_play_pause(self):
        """Toggle between play and pause states."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def on_playback_state_changed(self, state):
        """Update play/pause button text based on playback state."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_btn.setText("⏸ Pause")
            self.loading_overlay.hide()  # Hide loading when playing
        else:
            self.play_pause_btn.setText("▶ Play")
    
    def on_buffer_progress(self, progress: float):
        """Handle buffer progress updates."""
        if progress < 1.0:  # progress is 0.0 to 1.0
            percent = int(progress * 100)
            self.loading_overlay.set_text(f"Buffering... {percent}%")
            self.loading_overlay.show()
        else:
            self.loading_overlay.hide()
    
    def on_media_status_changed(self, status):
        """Handle media status changes for loading states."""
        if status == QMediaPlayer.MediaStatus.LoadingMedia:
            self.loading_overlay.set_text("Loading video...")
            self.loading_overlay.show()
        elif status == QMediaPlayer.MediaStatus.BufferingMedia:
            self.loading_overlay.set_text("Buffering...")
            self.loading_overlay.show()
        elif status == QMediaPlayer.MediaStatus.BufferedMedia:
            self.loading_overlay.hide()
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.loading_overlay.hide()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.loading_overlay.set_text("Error loading video")
            # Hide after 2 seconds
            QTimer.singleShot(2000, self.loading_overlay.hide)
    
    def _translate_title_to_vietnamese(self, title: str) -> str:
        """Translate video title to Vietnamese using deep-translator."""
        if not title or not title.strip():
            return title
        
        try:
            from deep_translator import GoogleTranslator
            
            # Detect if title contains Chinese characters
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in title)
            # Detect if title is mostly ASCII (English)
            is_english = sum(1 for c in title if c.isascii() and c.isalpha()) / max(len(title), 1) > 0.5
            
            if has_chinese:
                # Translate from Chinese to Vietnamese
                translator = GoogleTranslator(source='zh-CN', target='vi')
                translated = translator.translate(title)
                print(f"🌐 Translated (ZH→VI): {title[:30]}... → {translated[:30]}...")
                return translated or title
            elif is_english:
                # Translate from English to Vietnamese
                translator = GoogleTranslator(source='en', target='vi')
                translated = translator.translate(title)
                print(f"🌐 Translated (EN→VI): {title[:30]}... → {translated[:30]}...")
                return translated or title
            else:
                # Auto-detect language
                translator = GoogleTranslator(source='auto', target='vi')
                translated = translator.translate(title)
                print(f"🌐 Translated (AUTO→VI): {title[:30]}... → {translated[:30]}...")
                return translated or title
                
        except Exception as e:
            print(f"⚠️ Translation failed: {e}. Using original title.")
            return title

    def cleanup(self):
        # Cleanup temp file
        if self.temp_preview_path and os.path.exists(self.temp_preview_path):
            try:
                os.remove(self.temp_preview_path)
            except:
                pass
