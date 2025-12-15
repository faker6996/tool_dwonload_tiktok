from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QWidget, QMessageBox
from PyQt6.QtCore import Qt
from src.ui.timeline.timeline_widget import TimelineWidget


class Timeline(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Worker references to prevent garbage collection
        self._transcription_worker = None
        self._tts_worker = None
        self._progress_dialog = None
        
        # Header
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Timeline")
        title.setObjectName("panel_title")
        header_layout.addWidget(title)
        
        # AI Tools Section
        ai_label = QLabel("AI Tools:")
        ai_label.setStyleSheet("color: #8b9dc3; margin-left: 10px;")
        header_layout.addWidget(ai_label)
        
        # Auto Sub Button (combines Generate + Remove subtitle features)
        self.caption_btn = QPushButton("📝 Auto Sub")
        self.caption_btn.setObjectName("primary")
        self.caption_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.caption_btn.clicked.connect(self.open_caption_dialog)
        header_layout.addWidget(self.caption_btn)
        
        # TTS Button
        self.tts_btn = QPushButton("🎤 Text to Speech")
        self.tts_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tts_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: 1px solid #3E3E3E;
            }
            QPushButton:hover {
                background-color: #3E3E3E;
                border-color: #505050;
            }
        """)
        self.tts_btn.clicked.connect(self.open_tts_dialog)
        header_layout.addWidget(self.tts_btn)
        
        header_layout.addStretch()
        
        layout.addWidget(header_container)
        
        # Timeline Widget
        self.timeline_widget = TimelineWidget()
        layout.addWidget(self.timeline_widget)

    def open_caption_dialog(self):
        """Open dialog to configure and run auto sub (transcribe, translate, or remove)."""
        from src.ui.dialogs.ai_dialogs import CaptionDialog
        
        # Check if there's a clip
        track = self.timeline_widget.main_track
        if not track.clips:
            QMessageBox.warning(self, "Auto Sub", "Không có video trong timeline.\nVui lòng thêm video trước.")
            return
        
        dialog = CaptionDialog(self)
        if dialog.exec():
            mode = dialog.get_mode()
            
            if mode == "remove":
                # Handle Remove Sub mode
                settings = dialog.get_remove_settings()
                self.start_subtitle_removal(settings)
            else:
                # Handle Transcribe or Translate mode
                language = dialog.get_language()
                translate_to = dialog.get_translate_to()
                self.start_transcription(language, translate_to)
    
    def start_transcription(self, language=None, translate_to=None):
        """Start transcription with progress dialog."""
        from src.ui.dialogs.ai_progress import AIProgressDialog, TranscriptionWorker
        
        print(f"[DEBUG] start_transcription called with language={language}, translate_to={translate_to}")
        
        track = self.timeline_widget.main_track
        if not track.clips:
            return
            
        clip = track.clips[0]
        
        # Store for retry with fallback
        self._current_clip = clip
        self._current_translate_to = translate_to
        self._current_language = language
        
        # Show progress dialog
        if translate_to:
            title = "🌐 Đang dịch..."
            msg = f"Transcribe và dịch sang {translate_to.upper()}"
        else:
            title = "🎯 Auto Caption"
            msg = "Đang transcribe audio..."
            
        self._progress_dialog = AIProgressDialog(self, title=title, message=msg)
        self._progress_dialog.set_status("⏳ Đang tải model AI...")
        
        # Create worker thread
        print(f"[DEBUG] Creating TranscriptionWorker with file={clip.asset_id}, translate_to={translate_to}")
        self._transcription_worker = TranscriptionWorker(clip.asset_id, language, translate_to)
        self._transcription_worker.progress.connect(self._on_transcription_progress)
        self._transcription_worker.finished.connect(self._on_transcription_finished)
        self._transcription_worker.error.connect(self._on_transcription_error)
        self._transcription_worker.rate_limit.connect(self._on_rate_limit)
        self._transcription_worker.start()
        
        self._progress_dialog.exec()
    
    def _on_transcription_progress(self, status: str):
        if self._progress_dialog:
            self._progress_dialog.set_status(status)
    
    def _on_transcription_finished(self, segments: list):
        if self._progress_dialog:
            self._progress_dialog.set_complete(True)
            self._progress_dialog.set_status(f"✅ Hoàn thành! Tạo được {len(segments)} đoạn subtitle.")
            
        if segments:
            track = self.timeline_widget.main_track
            if track.clips:
                clip = track.clips[0]
                self.timeline_widget.add_subtitle_track(segments, start_offset=clip.start_time)
            
            # Pass subtitles to Player for live display
            self._update_player_subtitles()
            
            # Show success message
            QMessageBox.information(
                self, 
                "Auto Caption", 
                f"✅ Đã tạo {len(segments)} đoạn subtitle!\n\n"
                f"📍 Subtitles sẽ hiển thị trên video khi play\n"
                f"💡 Click vào đoạn subtitle để xem nội dung trong Inspector"
            )
        else:
            QMessageBox.warning(self, "Auto Caption", "Không tìm thấy lời nói trong video.")
        
        if self._progress_dialog:
            self._progress_dialog.accept()
    
    def _update_player_subtitles(self):
        """Pass subtitle clips to Player for live display."""
        try:
            # Find parent edit_page to access player
            parent = self.parent()
            while parent:
                if hasattr(parent, 'player'):
                    # Get subtitle clips from timeline
                    for track in self.timeline_widget.tracks:
                        if track.name == "Subtitles":
                            parent.player.set_subtitles(track.clips)
                            print(f"Passed {len(track.clips)} subtitles to Player")
                            break
                    break
                parent = parent.parent()
        except Exception as e:
            print(f"Error updating player subtitles: {e}")
    
    def _on_transcription_error(self, error: str):
        if self._progress_dialog:
            self._progress_dialog.set_complete(False)
            self._progress_dialog.set_status(f"❌ Lỗi: {error}")
        
        QMessageBox.critical(self, "Auto Caption Error", f"Lỗi khi transcribe:\n{error}")
        
        if self._progress_dialog:
            self._progress_dialog.accept()
    
    def _on_rate_limit(self, provider: str):
        """Handle rate limit error - ask user if they want to fallback to Google Translate."""
        if self._progress_dialog:
            self._progress_dialog.hide()
        
        reply = QMessageBox.question(
            self,
            "⚠️ API Rate Limit",
            f"❌ {provider} đã hết quota miễn phí hôm nay!\n\n"
            f"Bạn có muốn dùng Google Translate (miễn phí, không giới hạn) để tiếp tục?\n\n"
            f"• Google Translate: Nhanh, miễn phí, chất lượng tốt\n"
            f"• Gemini Pro: Chờ đến ngày mai để reset quota",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Switch to Google Translate and retry
            from src.core.ai.translation import translation_service
            translation_service.set_provider("google")
            
            # Close old dialog
            if self._progress_dialog:
                self._progress_dialog.accept()
            
            # Restart with Google Translate
            print("🔄 Retrying with Google Translate...")
            self.start_transcription(self._current_language, self._current_translate_to)
        else:
            # User cancelled
            if self._progress_dialog:
                self._progress_dialog.set_complete(False)
                self._progress_dialog.set_status("❌ Đã hủy do rate limit")
                self._progress_dialog.accept()
            
            QMessageBox.information(
                self,
                "Thông báo",
                "Vui lòng thử lại sau hoặc dùng Google Translate trong cài đặt."
            )

    def open_tts_dialog(self):
        """Open TTS dialog with voice selection."""
        from src.ui.dialogs.ai_dialogs import TTSDialog
        
        dialog = TTSDialog(self)
        if dialog.exec():
            text = dialog.get_text()
            voice = dialog.get_voice()
            
            if text:
                self.start_tts(text, voice)
    
    def start_tts(self, text: str, voice: str):
        """Start TTS generation with progress dialog."""
        from src.ui.dialogs.ai_progress import AIProgressDialog, TTSWorker
        import os
        import tempfile
        import time
        
        # Generate output path
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"tts_{int(time.time())}.mp3")
        
        # Show progress dialog
        self._progress_dialog = AIProgressDialog(
            self, 
            title="🎤 Text to Speech",
            message="Đang tạo giọng nói..."
        )
        self._progress_dialog.set_status(f"🔊 Voice: {voice}")
        
        # Create worker thread
        self._tts_worker = TTSWorker(text, output_path, voice)
        self._tts_worker.progress.connect(self._on_tts_progress)
        self._tts_worker.finished.connect(lambda path, dur: self._on_tts_finished(path, dur, text))
        self._tts_worker.error.connect(self._on_tts_error)
        self._tts_worker.start()
        
        self._progress_dialog.exec()
    
    def _on_tts_progress(self, status: str):
        if self._progress_dialog:
            self._progress_dialog.set_status(status)
    
    def _on_tts_finished(self, output_path: str, duration: float, text: str):
        from src.core.timeline.clip import Clip
        from src.core.timeline.track import Track
        
        if self._progress_dialog:
            self._progress_dialog.set_complete(True)
            self._progress_dialog.set_status(f"✅ Hoàn thành! Duration: {duration:.1f}s")
        
        # Find or create AI Voiceover track
        audio_track = None
        for track in self.timeline_widget.tracks:
            if track.name == "AI Voiceover":
                audio_track = track
                break
        
        if not audio_track:
            audio_track = Track("AI Voiceover", is_audio=True)
            self.timeline_widget.tracks.append(audio_track)
        
        # Create Clip
        clip = Clip(
            asset_id=output_path,
            name=f"🎤 {text[:20]}..." if len(text) > 20 else f"🎤 {text}",
            duration=duration,
            waveform_path=None
        )
        audio_track.clips.append(clip)
        
        self.timeline_widget.refresh_tracks()
        
        # Show success message
        QMessageBox.information(
            self, 
            "Text to Speech", 
            f"✅ Đã tạo audio thành công!\n\n"
            f"⏱ Duration: {duration:.1f} giây\n"
            f"📍 Xem kết quả: Track 'AI Voiceover' trong Timeline\n"
            f"🔊 Click Play để nghe audio"
        )
        
        if self._progress_dialog:
            self._progress_dialog.accept()
    
    def _on_tts_error(self, error: str):
        if self._progress_dialog:
            self._progress_dialog.set_complete(False)
            self._progress_dialog.set_status(f"❌ Lỗi: {error}")
        
        QMessageBox.critical(self, "TTS Error", f"Lỗi khi tạo giọng nói:\n{error}")
        
        if self._progress_dialog:
            self._progress_dialog.accept()

    def open_subtitle_removal_dialog(self):
        """Open dialog to configure subtitle removal."""
        from src.ui.dialogs.subtitle_removal_dialog import SubtitleRemovalDialog
        
        # Check if there's a clip
        track = self.timeline_widget.main_track
        if not track.clips:
            QMessageBox.warning(self, "Remove Subtitles", "Không có video trong timeline.\nVui lòng thêm video trước.")
            return
        
        dialog = SubtitleRemovalDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            if settings:
                self.start_subtitle_removal(settings)
    
    def start_subtitle_removal(self, settings: dict):
        """Start subtitle removal with progress dialog."""
        from src.ui.dialogs.ai_progress import AIProgressDialog
        from PyQt6.QtCore import QThread, pyqtSignal
        import os
        import time
        
        track = self.timeline_widget.main_track
        if not track.clips:
            return
        
        clip = track.clips[0]
        input_path = clip.asset_id
        
        # Generate output path
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.dirname(input_path)
        output_path = os.path.join(output_dir, f"{base_name}_no_sub.mp4")
        
        # Store for use in callbacks
        self._sub_removal_output = output_path
        self._sub_removal_settings = settings
        
        # Show progress dialog
        self._progress_dialog = AIProgressDialog(
            self, 
            title="🗑️ Removing Subtitles",
            message="Đang xoá subtitle từ video..."
        )
        self._progress_dialog.set_status("⏳ Đang xử lý...")
        
        # Create worker thread
        class SubtitleRemovalWorker(QThread):
            progress = pyqtSignal(str)
            finished = pyqtSignal(str)  # output path
            error = pyqtSignal(str)
            
            def __init__(self, input_path, output_path, settings):
                super().__init__()
                self.input_path = input_path
                self.output_path = output_path
                self.settings = settings
            
            def run(self):
                try:
                    from src.core.ai.subtitle_remover import subtitle_remover_service
                    
                    algorithm = self.settings.get("algorithm", "blur")
                    bottom_percent = self.settings.get("bottom_percent", 0.15)
                    
                    if algorithm == "inpaint":
                        # Use slow but high-quality OpenCV inpaint
                        self.progress.emit("🐢 AI Inpainting (sẽ mất 30+ phút)...")
                        success = subtitle_remover_service.process_video(
                            self.input_path,
                            self.output_path,
                            progress_callback=lambda c, t: self.progress.emit(f"⏳ Frame {c}/{t}"),
                            region=None  # Auto-detect
                        )
                    else:
                        # Use fast FFmpeg methods
                        self.progress.emit(f"🚀 Processing with FFmpeg ({algorithm})...")
                        success = subtitle_remover_service.remove_subtitles_ffmpeg(
                            self.input_path,
                            self.output_path,
                            bottom_percent=bottom_percent,
                            method=algorithm  # blur, black, or crop
                        )
                    
                    if success:
                        self.finished.emit(self.output_path)
                    else:
                        self.error.emit("Failed to process video")
                        
                except Exception as e:
                    self.error.emit(str(e))
        
        self._sub_removal_worker = SubtitleRemovalWorker(input_path, output_path, settings)
        self._sub_removal_worker.progress.connect(self._on_sub_removal_progress)
        self._sub_removal_worker.finished.connect(self._on_sub_removal_finished)
        self._sub_removal_worker.error.connect(self._on_sub_removal_error)
        self._sub_removal_worker.start()
        
        self._progress_dialog.exec()
    
    def _on_sub_removal_progress(self, status: str):
        if self._progress_dialog:
            self._progress_dialog.set_status(status)
    
    def _on_sub_removal_finished(self, output_path: str):
        if self._progress_dialog:
            self._progress_dialog.set_complete(True)
            self._progress_dialog.set_status("✅ Hoàn thành!")
        
        QMessageBox.information(
            self, 
            "Remove Subtitles", 
            f"✅ Đã xoá subtitle thành công!\n\n"
            f"📁 File mới: {os.path.basename(output_path)}\n"
            f"📍 Folder: {os.path.dirname(output_path)}"
        )
        
        if self._progress_dialog:
            self._progress_dialog.accept()
    
    def _on_sub_removal_error(self, error: str):
        if self._progress_dialog:
            self._progress_dialog.set_complete(False)
            self._progress_dialog.set_status(f"❌ Lỗi: {error}")
        
        QMessageBox.critical(self, "Remove Subtitles Error", f"Lỗi:\n{error}")
        
        if self._progress_dialog:
            self._progress_dialog.accept()
