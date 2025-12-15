import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QWidget, QMessageBox
from PyQt6.QtCore import Qt, pyqtSlot
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
        """Open dialog to configure and run auto sub (transcribe, translate, OCR, or remove)."""
        from src.ui.dialogs.ai_dialogs import CaptionDialog
        
        # Check if there's a clip
        track = self.timeline_widget.main_track
        if not track.clips:
            QMessageBox.warning(self, "Auto Sub", "Không có video trong timeline.\nVui lòng thêm video trước.")
            return
        
        dialog = CaptionDialog(self)
        if dialog.exec():
            mode = dialog.get_mode()  # "transcribe", "translate", or "ocr"
            remove_settings = dialog.get_remove_settings()  # None if checkbox not checked
            
            # Store params for after remove
            language = dialog.get_language()
            translate_to = dialog.get_translate_to()
            
            if mode == "ocr":
                # OCR Extract mode - read text from ORIGINAL video first
                # Then remove sub, then overlay translated subtitles
                self._pending_ocr_remove_settings = remove_settings  # Store for after OCR
                self._pending_ocr_translate_to = translate_to
                # Start OCR extraction on ORIGINAL video (not the removed one)
                self.start_ocr_extraction(translate_to, remove_after=bool(remove_settings))
            elif remove_settings:
                # Run remove sub first, then transcription
                self._pending_transcription = (language, translate_to)
                self.start_subtitle_removal(remove_settings, then_transcribe=True)
            else:
                # No remove, just transcribe/translate
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
        
        # No dialog - user wants to see progress in queue instead
        # Just print to console for debugging
        if translate_to:
            print(f"🌐 Starting transcription + translation to {translate_to.upper()}...")
        else:
            print(f"🎯 Starting transcription...")
        
        # Create worker thread
        print(f"[DEBUG] Creating TranscriptionWorker with file={clip.asset_id}, translate_to={translate_to}")
        self._transcription_worker = TranscriptionWorker(clip.asset_id, language, translate_to)
        self._transcription_worker.progress.connect(self._on_transcription_progress)
        self._transcription_worker.finished.connect(self._on_transcription_finished)
        self._transcription_worker.error.connect(self._on_transcription_error)
        self._transcription_worker.rate_limit.connect(self._on_rate_limit)
        self._transcription_worker.start()
    
    def start_ocr_extraction(self, translate_to=None, remove_after=False):
        """Start OCR subtitle extraction from video frames."""
        from PyQt6.QtCore import QThread, pyqtSignal
        
        print(f"👁️ Starting OCR subtitle extraction, translate_to={translate_to}, remove_after={remove_after}")
        
        track = self.timeline_widget.main_track
        if not track.clips:
            return
            
        clip = track.clips[0]
        video_path = clip.asset_id
        
        # Store for later (remove sub after OCR)
        self._ocr_original_video = video_path
        self._ocr_remove_after = remove_after
        
        # Create worker thread for OCR
        class OCRWorker(QThread):
            finished = pyqtSignal(list)
            error = pyqtSignal(str)
            progress = pyqtSignal(str)
            
            def __init__(self, video_path, translate_to):
                super().__init__()
                self.video_path = video_path
                self.translate_to = translate_to
            
            def run(self):
                try:
                    from src.core.ai.ocr_subtitle import ocr_subtitle_extractor
                    
                    self.progress.emit("🔍 Đang quét video với OCR...")
                    segments = ocr_subtitle_extractor.extract_subtitles(
                        self.video_path,
                        target_lang=self.translate_to or "vi",
                        fps_sample=1.0,  # 1 frame per second
                        translate=bool(self.translate_to)
                    )
                    self.finished.emit(segments)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self.error.emit(str(e))
        
        self._ocr_worker = OCRWorker(video_path, translate_to)
        self._ocr_worker.finished.connect(self._on_ocr_finished)
        self._ocr_worker.error.connect(self._on_ocr_error)
        self._ocr_worker.progress.connect(lambda msg: print(msg))
        self._ocr_worker.start()
    
    def _on_ocr_finished(self, segments: list):
        """Handle OCR extraction completion."""
        print(f"✅ OCR extraction complete! Found {len(segments)} subtitle segments.")
        
        if not segments:
            QMessageBox.warning(self, "OCR Extract", "Không tìm thấy text trong video.")
            return
        
        # Store OCR segments for later (after sub removal)
        self._ocr_segments = segments
        
        # Check if we need to remove sub first
        remove_after = getattr(self, '_ocr_remove_after', False)
        remove_settings = getattr(self, '_pending_ocr_remove_settings', None)
        
        if remove_after and remove_settings:
            # Remove sub from ORIGINAL video, then overlay new subtitles
            print(f"🗑️ Xoá sub gốc trước khi overlay subtitle mới...")
            # Set flag to overlay subtitles after removal completes
            self._then_overlay_ocr = True
            self.start_subtitle_removal(remove_settings, then_transcribe=False)
        else:
            # No removal needed - just add subtitles directly
            self._apply_ocr_subtitles(segments)
    
    def _apply_ocr_subtitles(self, segments: list):
        """Apply OCR extracted subtitles to timeline and player."""
        if not segments:
            return
        
        # Add subtitles to timeline
        track = self.timeline_widget.main_track
        if track.clips:
            clip = track.clips[0]
            self.timeline_widget.add_subtitle_track(segments, start_offset=clip.start_time)
        
        # Pass subtitles to Player
        self._update_player_subtitles()
        
        QMessageBox.information(
            self, 
            "OCR Extract", 
            f"✅ Đã trích xuất và overlay {len(segments)} đoạn subtitle!"
        )
    
    def _on_ocr_error(self, error: str):
        """Handle OCR extraction error."""
        print(f"❌ OCR error: {error}")
        QMessageBox.critical(self, "OCR Error", f"Lỗi khi trích xuất subtitle:\n{error}")
    
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
            
            # Check if we came from remove sub flow - load new video
            new_video_path = getattr(self, '_sub_removal_output', None)
            if new_video_path and os.path.exists(new_video_path):
                self._load_new_video_to_player_and_media(new_video_path)
                self._sub_removal_output = None  # Clear for next time
            
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
            self._progress_dialog.close()
    
    def _load_new_video_to_player_and_media(self, video_path: str):
        """Load the new (no-sub) video into player, media panel, and update timeline."""
        try:
            # Update timeline clip to use new video
            track = self.timeline_widget.main_track
            if track.clips:
                track.clips[0].asset_id = video_path
                track.clips[0].name = os.path.basename(video_path)
                self.timeline_widget.refresh_tracks()  # Correct method name
                print(f"✅ Updated timeline clip to: {os.path.basename(video_path)}")
            
            # Find parent edit_page to access player and media panel
            parent = self.parent()
            while parent:
                # Load video into player
                if hasattr(parent, 'player'):
                    if hasattr(parent.player, 'load_clip_from_path'):
                        parent.player.load_clip_from_path(video_path)
                        print(f"✅ Loaded new video into player: {os.path.basename(video_path)}")
                
                # Add to media panel
                if hasattr(parent, 'media_panel'):
                    if hasattr(parent.media_panel, 'import_media'):
                        parent.media_panel.import_media([video_path])
                        print(f"✅ Added video to media panel: {os.path.basename(video_path)}")
                    break
                
                parent = parent.parent()
        except Exception as e:
            print(f"Error loading new video: {e}")
            import traceback
            traceback.print_exc()
    
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
            self._progress_dialog.close()
    
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
                self._progress_dialog.close()
            
            # Restart with Google Translate
            print("🔄 Retrying with Google Translate...")
            self.start_transcription(self._current_language, self._current_translate_to)
        else:
            # User cancelled
            if self._progress_dialog:
                self._progress_dialog.set_complete(False)
                self._progress_dialog.set_status("❌ Đã hủy do rate limit")
                self._progress_dialog.close()
            
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
        """Start TTS generation using queue system (non-blocking)."""
        from src.core.queue_manager import queue_manager, TaskType
        import os
        import tempfile
        import time
        
        # Generate output path
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"tts_{int(time.time())}.mp3")
        
        # Register handler if not already done
        if not hasattr(self, '_tts_handler_registered'):
            self._register_tts_handler()
            self._tts_handler_registered = True
        
        # Add task to queue (non-blocking!)
        queue_manager.add_task(
            TaskType.TRANSLATE,  # Reuse TRANSLATE type for TTS
            f"TTS: {text[:30]}..." if len(text) > 30 else f"TTS: {text}",
            {
                "text": text,
                "voice": voice,
                "output_path": output_path,
                "timeline_ref": self
            }
        )
        
        # Show info message (non-blocking)
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            "Queue", 
            f"✅ Đã thêm vào queue!\n\n"
            f"📋 Task: Text to Speech\n"
            f"🔊 Voice: {voice}\n\n"
            f"💡 Theo dõi tiến trình trong Queue panel (nút 📋 trên header)"
        )
    
    def _register_tts_handler(self):
        """Register TTS handler with queue manager."""
        from src.core.queue_manager import queue_manager, TaskType
        
        def handle_tts(data: dict, progress_callback):
            from src.core.ai.tts import tts_service
            
            text = data["text"]
            voice = data["voice"]
            output_path = data["output_path"]
            
            progress_callback(20)
            
            # Generate TTS
            tts_service.generate_speech(text, output_path, voice=voice)
            
            progress_callback(80)
            
            # Get duration
            try:
                from mutagen.mp3 import MP3
                audio = MP3(output_path)
                duration = audio.info.length
            except:
                words = len(text.split())
                duration = max(1.0, words * 0.4)
            
            progress_callback(100)
            
            # Callback to add clip to timeline
            timeline_ref = data.get("timeline_ref")
            if timeline_ref:
                from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                # Store data for callback
                timeline_ref._tts_result = {
                    "output_path": output_path,
                    "duration": duration,
                    "text": text
                }
                QMetaObject.invokeMethod(
                    timeline_ref, 
                    "_on_queue_tts_complete",
                    Qt.ConnectionType.QueuedConnection
                )
        
        queue_manager.register_handler(TaskType.TRANSLATE, handle_tts)
    
    def _on_queue_tts_complete(self):
        """Called when queued TTS completes."""
        from src.core.timeline.clip import Clip
        from src.core.timeline.track import Track
        
        result = getattr(self, '_tts_result', None)
        if not result:
            return
        
        output_path = result["output_path"]
        duration = result["duration"]
        text = result["text"]
        
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
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            "Text to Speech", 
            f"✅ Đã tạo audio thành công!\n\n"
            f"⏱ Duration: {duration:.1f} giây\n"
            f"📍 Xem kết quả: Track 'AI Voiceover' trong Timeline"
        )
    
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
            self._progress_dialog.close()
    
    def _on_tts_error(self, error: str):
        if self._progress_dialog:
            self._progress_dialog.set_complete(False)
            self._progress_dialog.set_status(f"❌ Lỗi: {error}")
        
        QMessageBox.critical(self, "TTS Error", f"Lỗi khi tạo giọng nói:\n{error}")
        
        if self._progress_dialog:
            self._progress_dialog.close()

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
    
    def start_subtitle_removal(self, settings: dict, then_transcribe: bool = False):
        """Start subtitle removal using queue system (non-blocking)."""
        from src.core.queue_manager import queue_manager, TaskType
        import os
        
        track = self.timeline_widget.main_track
        if not track.clips:
            return
        
        clip = track.clips[0]
        input_path = clip.asset_id
        
        # Generate output path
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.dirname(input_path)
        output_path = os.path.join(output_dir, f"{base_name}_no_sub.mp4")
        
        # Store for callback
        self._sub_removal_output = output_path
        self._then_transcribe = then_transcribe
        if then_transcribe and hasattr(self, '_pending_transcription'):
            pass  # Keep pending transcription
        
        # Register handler if not already done
        if not hasattr(self, '_sub_handler_registered'):
            self._register_subtitle_removal_handler()
            self._sub_handler_registered = True
        
        # Add task to queue (non-blocking!)
        task = queue_manager.add_task(
            TaskType.REMOVE_SUB,
            f"Remove sub: {os.path.basename(input_path)}",
            {
                "input_path": input_path,
                "output_path": output_path,
                "settings": settings,
                "then_transcribe": then_transcribe,
                "timeline_ref": self  # Reference for callback
            }
        )
        
        # Show info message (non-blocking)
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            "Queue", 
            f"✅ Đã thêm vào queue!\n\n"
            f"📋 Task: Remove Subtitles\n"
            f"📁 File: {os.path.basename(input_path)}\n\n"
            f"💡 Theo dõi tiến trình trong Queue panel (nút 📋 trên header)"
        )
    
    def _register_subtitle_removal_handler(self):
        """Register subtitle removal handler with queue manager."""
        from src.core.queue_manager import queue_manager, TaskType
        
        def handle_remove_sub(data: dict, progress_callback):
            from src.core.ai.subtitle_remover import subtitle_remover_service
            
            input_path = data["input_path"]
            output_path = data["output_path"]
            settings = data["settings"]
            
            algorithm = settings.get("algorithm", "blur")
            bottom_percent = settings.get("bottom_percent", 0.15)
            
            progress_callback(10)
            
            if algorithm == "inpaint":
                progress_callback(20)
                success = subtitle_remover_service.process_video(
                    input_path, output_path,
                    progress_callback=lambda c, t: progress_callback(20 + int(c/t * 70)),
                    region=None
                )
            else:
                progress_callback(30)
                success = subtitle_remover_service.remove_subtitles_ffmpeg(
                    input_path, output_path,
                    bottom_percent=bottom_percent,
                    method=algorithm
                )
            
            if not success:
                raise Exception("Failed to process video")
            
            progress_callback(100)
            
            # Handle callback - always notify timeline that removal is complete
            timeline_ref = data.get("timeline_ref")
            if timeline_ref:
                # Update clip and chain next action (transcription or OCR)
                from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(
                    timeline_ref, 
                    "_on_queue_sub_removal_complete",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, output_path)
                )
        
        queue_manager.register_handler(TaskType.REMOVE_SUB, handle_remove_sub)
    
    @pyqtSlot(str)
    def _on_queue_sub_removal_complete(self, output_path: str):
        """Called when queued subtitle removal completes."""
        import os
        
        # Update clip to use new video
        track = self.timeline_widget.main_track
        if track.clips:
            track.clips[0].asset_id = output_path
            track.clips[0].name = os.path.basename(output_path)
        
        # Store path for transcription callback
        self._sub_removal_output = output_path
        
        # Load new video into player and media pool
        self._load_new_video_to_player_and_media(output_path)
        
        # Check if we need to overlay OCR extracted subtitles
        if getattr(self, '_then_overlay_ocr', False) and hasattr(self, '_ocr_segments'):
            print(f"✅ Xoá subtitle thành công! Overlay subtitle OCR đã dịch...")
            self._then_overlay_ocr = False
            segments = self._ocr_segments
            self._ocr_segments = None
            self._apply_ocr_subtitles(segments)
        # Check if OCR extraction was requested (legacy flow)
        elif getattr(self, '_then_ocr', False) and hasattr(self, '_pending_ocr'):
            translate_to = self._pending_ocr[0]
            print(f"✅ Xoá subtitle thành công! Tiếp tục OCR extraction...")
            self._then_ocr = False
            self.start_ocr_extraction(translate_to)
        # Chain transcription if requested
        elif getattr(self, '_then_transcribe', False) and hasattr(self, '_pending_transcription'):
            language, translate_to = self._pending_transcription
            print(f"✅ Xoá subtitle thành công! Tiếp tục transcription...")
            self._then_transcribe = False
            self.start_transcription(language, translate_to)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Remove Subtitles",
                f"✅ Đã xoá subtitle thành công!\n\n"
                f"📁 File mới: {os.path.basename(output_path)}"
            )
    
    def _on_sub_removal_progress(self, status: str):
        if self._progress_dialog:
            self._progress_dialog.set_status(status)
    
    def _on_sub_removal_finished(self, output_path: str):
        if self._progress_dialog:
            self._progress_dialog.set_complete(True)
            self._progress_dialog.set_status("✅ Hoàn thành!")
            self._progress_dialog.close()
        
        # Check if we should chain transcription
        if getattr(self, '_then_transcribe', False) and hasattr(self, '_pending_transcription'):
            # Update clip to use the new video without subs
            track = self.timeline_widget.main_track
            if track.clips:
                track.clips[0].asset_id = output_path
            
            # Chain transcription automatically (no confirmation needed)
            language, translate_to = self._pending_transcription
            print(f"✅ Xoá subtitle thành công! Tiếp tục transcription...")
            self._then_transcribe = False
            self.start_transcription(language, translate_to)
        else:
            # Show message only if not chaining
            QMessageBox.information(
                self, 
                "Remove Subtitles", 
                f"✅ Đã xoá subtitle thành công!\n\n"
                f"📁 File mới: {os.path.basename(output_path)}\n"
                f"📍 Folder: {os.path.dirname(output_path)}"
            )
    
    def _on_sub_removal_error(self, error: str):
        if self._progress_dialog:
            self._progress_dialog.set_complete(False)
            self._progress_dialog.set_status(f"❌ Lỗi: {error}")
        
        QMessageBox.critical(self, "Remove Subtitles Error", f"Lỗi:\n{error}")
        
        if self._progress_dialog:
            self._progress_dialog.close()
