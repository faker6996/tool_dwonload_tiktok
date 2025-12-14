from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSlider, QWidget, QInputDialog
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
        self.caption_btn.clicked.connect(self.generate_captions)
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

    def generate_captions(self):
        # Get selected clip
        # For MVP, we just take the first clip in main track if nothing selected
        # Or better, we need access to selection.
        # Let's assume we caption the first clip in main track for now.
        
        track = self.timeline_widget.main_track
        if not track.clips:
            print("No clips to caption")
            return
            
        clip = track.clips[0]
        
        # Call Transcription Service
        from src.core.ai.transcription import transcription_service
        segments = transcription_service.transcribe(clip.asset_id)
        
        # Create Subtitle Track if needed
        # For MVP, we'll just add to a new track or the main track (if we support layers)
        # Let's add to a new "Subtitle" track in TimelineWidget
        
        self.timeline_widget.add_subtitle_track(segments, start_offset=clip.start_time)

    def open_tts_dialog(self):
        text, ok = QInputDialog.getText(self, "Text to Speech", "Enter text to generate speech (Vietnamese/English):")
        if ok and text:
            from src.core.ai.tts import tts_service
            import os
            import tempfile
            import time
            from src.core.timeline.clip import Clip
            from src.core.timeline.track import Track
            
            # Generate Audio (edge-tts generates MP3)
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"tts_{int(time.time())}.mp3")
            
            try:
                tts_service.generate_speech(text, output_path)
                
                # Get actual audio duration using mutagen if available, otherwise estimate
                try:
                    from mutagen.mp3 import MP3
                    audio = MP3(output_path)
                    duration = audio.info.length
                except:
                    # Fallback: estimate based on text length
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
                print(f"TTS audio added: {duration:.1f}s")
                
            except Exception as e:
                print(f"TTS Error: {e}")

