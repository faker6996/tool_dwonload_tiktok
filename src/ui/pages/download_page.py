from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
                             QLabel, QFrame, QProgressBar, QFileDialog, QMessageBox,
                             QGraphicsOpacityEffect, QTableWidget, QTableWidgetItem,
                             QHeaderView, QCheckBox, QSpinBox, QGroupBox)
from PyQt6.QtCore import Qt, QUrl, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QMovie, QPainter, QColor, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from src.core.manager import DownloaderManager
from src.ui.widgets.bounded_combobox import BoundedComboBox
from ..threads import AnalyzerThread, PreviewDownloaderThread, DownloaderThread, ChannelScraperThread
import os


class LoadingOverlay(QWidget):
    """Semi-transparent overlay with loading spinner and status text."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.spinner_label = QLabel()
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinner_label.setStyleSheet("font-size: 48px; color: #3498db;")
        layout.addWidget(self.spinner_label)
        
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
        
        self.spinner_frame = 0
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self._update_spinner)
        
    def showEvent(self, event):
        super().showEvent(event)
        self.spinner_timer.start(150)
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
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))


class DownloadPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # State
        self.current_video_url = None
        self.current_platform = None
        self.current_cookies = None
        self.temp_preview_path = None
        self.video_title = None
        self.channel_videos = []  # List of videos from channel scan

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        title_label = QLabel("Download Video")
        title_label.setObjectName("page_title")
        layout.addWidget(title_label)

        # Mode Selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        
        self.mode_combo = BoundedComboBox()
        self.mode_combo.addItems([
            "📹 Single Video",
            "📂 Bulk from Channel",
            "📄 Import from File"
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # === Single Video Mode ===
        self.single_widget = QWidget()
        single_layout = QVBoxLayout(self.single_widget)
        single_layout.setContentsMargins(0, 0, 0, 0)
        
        # URL Input
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
        single_layout.addLayout(input_layout)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888888;")
        single_layout.addWidget(self.status_label)

        # Preview Area
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("preview_frame")
        self.preview_frame.setMinimumHeight(350)
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget()
        preview_layout.addWidget(self.video_widget)
        
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        self.play_pause_btn = QPushButton("▶ Play")
        self.play_pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_pause_btn.setFixedWidth(100)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.play_pause_btn.setEnabled(False)
        controls_layout.addWidget(self.play_pause_btn)
        
        controls_layout.addStretch()

        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("color: #a1a1aa;")
        controls_layout.addWidget(speed_label)

        self.playback_rate_combo = BoundedComboBox()
        self.playback_rate_combo.setFixedWidth(90)
        self.playback_rate_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.playback_rate_combo.setToolTip("Playback speed (preview only)")
        self.playback_rate_combo.addItem("0.5x", 0.5)
        self.playback_rate_combo.addItem("0.75x", 0.75)
        self.playback_rate_combo.addItem("1.0x", 1.0)
        self.playback_rate_combo.addItem("1.25x", 1.25)
        self.playback_rate_combo.addItem("1.5x", 1.5)
        self.playback_rate_combo.addItem("2.0x", 2.0)
        self.playback_rate_combo.setCurrentIndex(2)  # 1.0x
        self.playback_rate_combo.currentIndexChanged.connect(self._apply_playback_rate)
        self.playback_rate_combo.setEnabled(False)
        controls_layout.addWidget(self.playback_rate_combo)

        preview_layout.addLayout(controls_layout)
        
        single_layout.addWidget(self.preview_frame)
        
        self.loading_overlay = LoadingOverlay(self.preview_frame)
        self.loading_overlay.hide()

        # Download Button
        action_layout = QHBoxLayout()
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
        single_layout.addLayout(action_layout)
        
        layout.addWidget(self.single_widget)

        # === Bulk Channel Mode ===
        self.bulk_widget = QWidget()
        bulk_layout = QVBoxLayout(self.bulk_widget)
        bulk_layout.setContentsMargins(0, 0, 0, 0)
        
        # Channel URL Input
        channel_input_layout = QHBoxLayout()
        self.channel_url_input = QLineEdit()
        self.channel_url_input.setPlaceholderText("Paste TikTok channel URL (e.g., https://www.tiktok.com/@username)")
        
        self.scan_btn = QPushButton("🔍 Scan Channel")
        self.scan_btn.setObjectName("primary")
        self.scan_btn.clicked.connect(self._scan_channel)
        
        channel_input_layout.addWidget(self.channel_url_input)
        channel_input_layout.addWidget(self.scan_btn)
        bulk_layout.addLayout(channel_input_layout)
        
        # Options
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Max videos:"))
        self.max_videos_spin = QSpinBox()
        self.max_videos_spin.setRange(1, 500)
        self.max_videos_spin.setValue(50)
        options_layout.addWidget(self.max_videos_spin)
        
        options_layout.addSpacing(20)
        
        self.filter_days_check = QCheckBox("Only last")
        options_layout.addWidget(self.filter_days_check)
        self.filter_days_spin = QSpinBox()
        self.filter_days_spin.setRange(1, 365)
        self.filter_days_spin.setValue(7)
        self.filter_days_spin.setEnabled(False)
        self.filter_days_check.toggled.connect(self.filter_days_spin.setEnabled)
        options_layout.addWidget(self.filter_days_spin)
        options_layout.addWidget(QLabel("days"))
        
        options_layout.addStretch()
        bulk_layout.addLayout(options_layout)
        
        # Status
        self.bulk_status_label = QLabel("Enter a channel URL and click Scan")
        self.bulk_status_label.setStyleSheet("color: #888888; padding: 5px;")
        bulk_layout.addWidget(self.bulk_status_label)
        
        # Video List Table
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(4)
        self.video_table.setHorizontalHeaderLabels(["✓", "Title", "URL", "Status"])
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.video_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.video_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.video_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.video_table.setColumnWidth(0, 30)
        self.video_table.setColumnWidth(3, 100)
        self.video_table.setMinimumHeight(250)
        bulk_layout.addWidget(self.video_table)
        
        # Bulk Actions
        bulk_action_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("☑ Select All")
        self.select_all_btn.clicked.connect(self._select_all_videos)
        bulk_action_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("☐ Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all_videos)
        bulk_action_layout.addWidget(self.deselect_all_btn)
        
        bulk_action_layout.addStretch()
        
        self.bulk_progress = QProgressBar()
        self.bulk_progress.setMinimumWidth(150)
        self.bulk_progress.setVisible(False)
        bulk_action_layout.addWidget(self.bulk_progress)
        
        self.download_all_btn = QPushButton("⬇ Download Selected")
        self.download_all_btn.setObjectName("primary")
        self.download_all_btn.setEnabled(False)
        self.download_all_btn.clicked.connect(self._download_selected)
        bulk_action_layout.addWidget(self.download_all_btn)
        
        bulk_layout.addLayout(bulk_action_layout)
        
        layout.addWidget(self.bulk_widget)
        self.bulk_widget.hide()

        # === Import File Mode ===
        self.import_widget = QWidget()
        import_layout = QVBoxLayout(self.import_widget)
        import_layout.setContentsMargins(0, 0, 0, 0)
        
        import_input_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select Excel/CSV file with video URLs...")
        self.file_path_input.setReadOnly(True)
        
        self.browse_file_btn = QPushButton("📁 Browse")
        self.browse_file_btn.clicked.connect(self._browse_file)
        
        self.import_btn = QPushButton("📥 Import")
        self.import_btn.setObjectName("primary")
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._import_file)
        
        import_input_layout.addWidget(self.file_path_input)
        import_input_layout.addWidget(self.browse_file_btn)
        import_input_layout.addWidget(self.import_btn)
        import_layout.addLayout(import_input_layout)
        
        # Info label
        import_info = QLabel("Supported: .xlsx, .csv with URLs in first column")
        import_info.setStyleSheet("color: #888888; font-size: 12px;")
        import_layout.addWidget(import_info)
        
        import_layout.addStretch()
        
        layout.addWidget(self.import_widget)
        self.import_widget.hide()

        # Initialize components
        self.downloader = DownloaderManager()
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.media_player.bufferProgressChanged.connect(self.on_buffer_progress)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)

    def _on_mode_changed(self, index):
        """Switch between download modes."""
        self.single_widget.setVisible(index == 0)
        self.bulk_widget.setVisible(index == 1)
        self.import_widget.setVisible(index == 2)
    
    # === Single Video Methods ===
    def analyze_url(self):
        text = self.url_input.text().strip()
        if not text:
            return

        import re
        url_match = re.search(r'https?://[^\s]+', text)
        if url_match:
            url = url_match.group(0)
        else:
            url = text

        self.status_label.setText("Analyzing URL... Please wait.")
        self.analyze_btn.setEnabled(False)
        self.url_input.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.media_player.stop()
        self.play_pause_btn.setEnabled(False)
        if hasattr(self, "playback_rate_combo"):
            self.playback_rate_combo.setEnabled(False)
        self.temp_preview_path = None
        
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
            self.video_title = info.get('title', '')
            
            self.loading_overlay.set_text("📥 Downloading preview...")
            
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
            if hasattr(self, "playback_rate_combo"):
                self.playback_rate_combo.setEnabled(True)
            
            self.media_player.setSource(QUrl.fromLocalFile(path))
            self._apply_playback_rate()
            self.media_player.play()
        else:
            self.status_label.setText("Could not load preview.")
            QMessageBox.warning(self, "Preview Error", "Could not load video preview, but you can try to download it directly.")
            self.download_btn.setEnabled(True)
            if hasattr(self, "playback_rate_combo"):
                self.playback_rate_combo.setEnabled(False)

    def reset_ui_state(self):
        self.analyze_btn.setEnabled(True)
        self.url_input.setEnabled(True)

    def _apply_playback_rate(self):
        """Apply preview-only playback speed to the media player."""
        rate = 1.0
        try:
            if hasattr(self, "playback_rate_combo"):
                data = self.playback_rate_combo.currentData()
                if data is not None:
                    rate = float(data)
            self.media_player.setPlaybackRate(rate)
        except Exception:
            # Keep UI responsive even if backend rejects the rate.
            pass

    def download_video(self):
        if not self.current_video_url:
            return

        import re
        import time
        
        if self.video_title:
            translated_title = self._translate_title_to_vietnamese(self.video_title)
            safe_title = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF\u4e00-\u9fff-]', '', translated_title)
            safe_title = safe_title.strip()[:80]
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
            self.progress_bar.setRange(0, 0)
            
            self.downloader_thread = DownloaderThread(self.current_video_url, filename, self.current_platform, self.temp_preview_path, self.current_cookies)
            self.downloader_thread.finished.connect(self.on_download_finished)
            self.downloader_thread.start()

    def on_download_finished(self, success, filename):
        self.download_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.media_player.pause()
        
        if success:
            self.status_label.setText("Saved successfully!")
            QMessageBox.information(self, "Success", f"Video saved to:\n{filename}")
        else:
            self.status_label.setText("Save failed.")
            QMessageBox.critical(self, "Error", "Failed to save video.")
    
    def toggle_play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_btn.setText("⏸ Pause")
            self.loading_overlay.hide()
        else:
            self.play_pause_btn.setText("▶ Play")
    
    def on_buffer_progress(self, progress: float):
        if progress < 1.0:
            percent = int(progress * 100)
            self.loading_overlay.set_text(f"Buffering... {percent}%")
            self.loading_overlay.show()
        else:
            self.loading_overlay.hide()
    
    def on_media_status_changed(self, status):
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
            QTimer.singleShot(2000, self.loading_overlay.hide)
    
    def _translate_title_to_vietnamese(self, title: str) -> str:
        if not title or not title.strip():
            return title
        
        try:
            from deep_translator import GoogleTranslator
            
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in title)
            is_english = sum(1 for c in title if c.isascii() and c.isalpha()) / max(len(title), 1) > 0.5
            
            if has_chinese:
                translator = GoogleTranslator(source='zh-CN', target='vi')
                translated = translator.translate(title)
                return translated or title
            elif is_english:
                translator = GoogleTranslator(source='en', target='vi')
                translated = translator.translate(title)
                return translated or title
            else:
                translator = GoogleTranslator(source='auto', target='vi')
                translated = translator.translate(title)
                return translated or title
                
        except Exception as e:
            print(f"⚠️ Translation failed: {e}")
            return title

    # === Bulk Channel Methods ===
    def _scan_channel(self):
        """Scan TikTok channel for videos."""
        channel_url = self.channel_url_input.text().strip()
        if not channel_url:
            QMessageBox.warning(self, "Error", "Please enter a channel URL")
            return
        
        # Validate URL
        if not ('tiktok.com/@' in channel_url or 'douyin.com/' in channel_url):
            QMessageBox.warning(self, "Error", "Invalid channel URL. Should be like: https://www.tiktok.com/@username")
            return
        
        self.scan_btn.setEnabled(False)
        self.bulk_status_label.setText("🔍 Scanning channel...")
        self.video_table.setRowCount(0)
        self.channel_videos = []
        
        max_videos = self.max_videos_spin.value()
        days_filter = self.filter_days_spin.value() if self.filter_days_check.isChecked() else None
        
        self.scraper_thread = ChannelScraperThread(channel_url, max_videos, days_filter)
        self.scraper_thread.progress.connect(self._on_scrape_progress)
        self.scraper_thread.finished.connect(self._on_scrape_finished)
        self.scraper_thread.error.connect(self._on_scrape_error)
        self.scraper_thread.start()
    
    def _on_scrape_progress(self, status: str, count: int):
        self.bulk_status_label.setText(status)
    
    def _on_scrape_finished(self, videos: list):
        self.scan_btn.setEnabled(True)
        self.channel_videos = videos
        
        if not videos:
            self.bulk_status_label.setText("No videos found. Try a different channel.")
            return
        
        self.bulk_status_label.setText(f"Found {len(videos)} videos. Select and download.")
        self.download_all_btn.setEnabled(True)
        
        # Populate table
        self.video_table.setRowCount(len(videos))
        for i, video in enumerate(videos):
            # Checkbox
            checkbox = QTableWidgetItem()
            checkbox.setCheckState(Qt.CheckState.Checked)
            self.video_table.setItem(i, 0, checkbox)
            
            # Title
            title_item = QTableWidgetItem(video.get('title', f'Video {i+1}'))
            self.video_table.setItem(i, 1, title_item)
            
            # URL
            url_item = QTableWidgetItem(video.get('url', ''))
            self.video_table.setItem(i, 2, url_item)
            
            # Status
            status_item = QTableWidgetItem("⏸ Pending")
            self.video_table.setItem(i, 3, status_item)
    
    def _on_scrape_error(self, error: str):
        self.scan_btn.setEnabled(True)
        self.bulk_status_label.setText(f"Error: {error}")
        QMessageBox.critical(self, "Scan Error", f"Failed to scan channel:\n{error}")
    
    def _select_all_videos(self):
        for i in range(self.video_table.rowCount()):
            item = self.video_table.item(i, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
    
    def _deselect_all_videos(self):
        for i in range(self.video_table.rowCount()):
            item = self.video_table.item(i, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
    
    def _download_selected(self):
        """Download all selected videos."""
        # Get selected videos
        selected = []
        for i in range(self.video_table.rowCount()):
            checkbox = self.video_table.item(i, 0)
            if checkbox and checkbox.checkState() == Qt.CheckState.Checked:
                url = self.video_table.item(i, 2).text() if self.video_table.item(i, 2) else ""
                if url:
                    selected.append((i, url))
        
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one video to download.")
            return
        
        # Ask for output folder
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if not folder:
            return
        
        self.download_all_btn.setEnabled(False)
        self.bulk_progress.setVisible(True)
        self.bulk_progress.setRange(0, len(selected))
        self.bulk_progress.setValue(0)
        
        # Start bulk download
        self._bulk_download_queue = selected
        self._bulk_download_folder = folder
        self._bulk_download_index = 0
        self._download_next_in_queue()
    
    def _download_next_in_queue(self):
        """Download next video in bulk queue."""
        if self._bulk_download_index >= len(self._bulk_download_queue):
            # Done
            self.bulk_progress.setVisible(False)
            self.download_all_btn.setEnabled(True)
            self.bulk_status_label.setText(f"✅ Downloaded {len(self._bulk_download_queue)} videos!")
            QMessageBox.information(self, "Complete", f"Downloaded {len(self._bulk_download_queue)} videos to:\n{self._bulk_download_folder}")
            return
        
        row_index, url = self._bulk_download_queue[self._bulk_download_index]
        
        # Update status in table
        status_item = self.video_table.item(row_index, 3)
        if status_item:
            status_item.setText("⏳ Downloading...")
        
        self.bulk_status_label.setText(f"Downloading {self._bulk_download_index + 1}/{len(self._bulk_download_queue)}...")
        
        # Generate filename
        title = self.video_table.item(row_index, 1).text() if self.video_table.item(row_index, 1) else f"video_{self._bulk_download_index}"
        import re
        safe_title = re.sub(r'[^\w\s-]', '', title)[:50]
        filename = os.path.join(self._bulk_download_folder, f"{safe_title}.mp4")
        
        # Start download thread
        self._current_bulk_row = row_index
        self.bulk_downloader_thread = DownloaderThread(url, filename, "tiktok", None, None)
        self.bulk_downloader_thread.finished.connect(self._on_bulk_download_finished)
        self.bulk_downloader_thread.start()
    
    def _on_bulk_download_finished(self, success: bool, filename: str):
        """Handle completion of one bulk download."""
        status_item = self.video_table.item(self._current_bulk_row, 3)
        if status_item:
            status_item.setText("✅ Done" if success else "❌ Failed")
        
        self._bulk_download_index += 1
        self.bulk_progress.setValue(self._bulk_download_index)
        
        # Add delay before next download to avoid rate limiting
        QTimer.singleShot(2000, self._download_next_in_queue)
    
    # === Import File Methods ===
    def _browse_file(self):
        """Browse for Excel/CSV file."""
        file_filter = "Excel/CSV Files (*.xlsx *.xls *.csv)"
        filepath, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)
        if filepath:
            self.file_path_input.setText(filepath)
            self.import_btn.setEnabled(True)
    
    def _import_file(self):
        """Import URLs from file and add to table."""
        filepath = self.file_path_input.text()
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(self, "Error", "Please select a valid file")
            return
        
        urls = []
        try:
            if filepath.endswith('.csv'):
                import csv
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0].startswith('http'):
                            urls.append(row[0])
            else:
                # Excel
                import openpyxl
                wb = openpyxl.load_workbook(filepath)
                sheet = wb.active
                for row in sheet.iter_rows(min_col=1, max_col=1, values_only=True):
                    if row[0] and str(row[0]).startswith('http'):
                        urls.append(str(row[0]))
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to read file:\n{e}")
            return
        
        if not urls:
            QMessageBox.warning(self, "No URLs", "No valid URLs found in the file.")
            return
        
        # Switch to bulk mode and populate table
        self.mode_combo.setCurrentIndex(1)  # Switch to bulk mode
        self._on_mode_changed(1)
        
        self.channel_videos = [{'url': url, 'title': f'Video {i+1}'} for i, url in enumerate(urls)]
        self._on_scrape_finished(self.channel_videos)
        
        QMessageBox.information(self, "Import Complete", f"Imported {len(urls)} URLs. Ready to download.")

    def cleanup(self):
        if self.temp_preview_path and os.path.exists(self.temp_preview_path):
            try:
                os.remove(self.temp_preview_path)
            except:
                pass
