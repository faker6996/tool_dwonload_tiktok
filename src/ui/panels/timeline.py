from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSlider, QWidget, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt
from src.ui.timeline.timeline_widget import TimelineWidget


class Timeline(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
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
        
        # Auto Caption Button
        self.caption_btn = QPushButton("🎯 Auto Caption")
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
        """Open dialog to configure and run auto caption."""
        from src.ui.dialogs.ai_dialogs import CaptionDialog
        
        # Check if there's a clip to caption
        track = self.timeline_widget.main_track
        if not track.clips:
            QMessageBox.warning(self, "Auto Caption", "Không có video trong timeline.\nVui lòng thêm video trước.")
            return
        
        dialog = CaptionDialog(self)
        if dialog.exec():
            language = dialog.get_language()
            translate_to = dialog.get_translate_to()
            self.generate_captions(language, translate_to)
    
    def generate_captions(self, language=None, translate_to=None):
        """Run transcription with selected language and optional translation."""
        track = self.timeline_widget.main_track
        if not track.clips:
            return
            
        clip = track.clips[0]
        
        from src.core.ai.transcription import transcription_service
        
        if translate_to:
            # Translate mode: transcribe then translate
            print(f"Starting transcription + translation to: {translate_to}")
            segments = transcription_service.transcribe_and_translate(clip.asset_id, target_language=translate_to)
        else:
            # Transcribe mode: just transcribe in specified language
            print(f"Starting transcription with language: {language or 'auto-detect'}")
            segments = transcription_service.transcribe(clip.asset_id, language=language)
        
        if segments:
            self.timeline_widget.add_subtitle_track(segments, start_offset=clip.start_time)
            print(f"Added {len(segments)} subtitle clips")
        else:
            QMessageBox.warning(self, "Auto Caption", "Không thể tạo caption. Kiểm tra file video.")

    def open_tts_dialog(self):
        """Open TTS dialog with voice selection."""
        from src.ui.dialogs.ai_dialogs import TTSDialog
        
        dialog = TTSDialog(self)
        if dialog.exec():
            text = dialog.get_text()
            voice = dialog.get_voice()
            
            if text:
                self.generate_tts(text, voice)
    
    def generate_tts(self, text: str, voice: str):
        """Generate TTS audio with selected voice."""
        from src.core.ai.tts import tts_service
        import os
        import tempfile
        import time
        from src.core.timeline.clip import Clip
        from src.core.timeline.track import Track
        
        # Generate Audio
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"tts_{int(time.time())}.mp3")
        
        try:
            tts_service.generate_speech(text, output_path, voice=voice)
            
            # Get audio duration
            try:
                from mutagen.mp3 import MP3
                audio = MP3(output_path)
                duration = audio.info.length
            except:
                words = len(text.split())
                duration = max(1.0, words * 0.4)
            
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
            print(f"TTS audio added: {duration:.1f}s with voice: {voice}")
            
        except Exception as e:
            print(f"TTS Error: {e}")
            QMessageBox.critical(self, "TTS Error", f"Không thể tạo audio:\n{str(e)}")
