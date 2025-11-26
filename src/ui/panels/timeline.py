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
        
        # Separator
        separator1 = QWidget()
        separator1.setFixedWidth(2)
        separator1.setStyleSheet("background-color: #3E3E3E;")
        header_layout.addWidget(separator1)
        
        # Zoom Controls
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("color: #8b9dc3; margin-left: 10px;")
        header_layout.addWidget(zoom_label)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(1, 100)
        self.zoom_slider.setValue(20)
        self.zoom_slider.setFixedWidth(120)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        header_layout.addWidget(self.zoom_slider)
        
        # Separator
        separator2 = QWidget()
        separator2.setFixedWidth(2)
        separator2.setStyleSheet("background-color: #3E3E3E;")
        header_layout.addWidget(separator2)
        
        # AI Tools Section
        ai_label = QLabel("AI Tools:")
        ai_label.setStyleSheet("color: #8b9dc3; margin-left: 10px;")
        header_layout.addWidget(ai_label)
        
        # Auto Caption Button
        self.caption_btn = QPushButton("🎯 Auto Caption")
        self.caption_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2D5F9E, stop:1 #5C3D99);
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3A7BC8, stop:1 #7350B3);
            }
        """)
        self.caption_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.caption_btn.clicked.connect(self.generate_captions)
        header_layout.addWidget(self.caption_btn)
        
        # TTS Button
        self.tts_btn = QPushButton("🎤 Text to Speech")
        self.tts_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2D9E73, stop:1 #3D7C99);
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3AC894, stop:1 #5096B3);
            }
        """)
        self.tts_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tts_btn.clicked.connect(self.open_tts_dialog)
        header_layout.addWidget(self.tts_btn)
        
        header_layout.addStretch()
        
        layout.addWidget(header_container)
        
        # Timeline Widget
        self.timeline_widget = TimelineWidget()
        layout.addWidget(self.timeline_widget)

    def on_zoom_changed(self, value):
        self.timeline_widget.set_zoom(value)

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
        text, ok = QInputDialog.getText(self, "Text to Speech", "Enter text to generate speech:")
        if ok and text:
            from src.core.ai.tts import tts_service
            import os
            import tempfile
            from src.core.timeline.clip import Clip
            from src.core.timeline.track import Track
            
            # Generate Audio
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"tts_{int(time.time())}.wav")
            import time # Need time import inside or top level
            
            tts_service.generate_speech(text, output_path)
            
            # Add to Timeline (New Audio Track)
            # Create Audio Track if not exists
            # For MVP, just append a new track
            audio_track = Track("AI Voiceover", is_audio=True)
            self.timeline_widget.tracks.append(audio_track)
            
            # Create Clip
            # We need duration. TTSService logic: max(1.0, words * 0.5)
            words = len(text.split())
            duration = max(1.0, words * 0.5)
            
            clip = Clip(
                asset_id=output_path,
                name=f"TTS: {text[:10]}...",
                duration=duration,
                waveform_path=None # TODO: Generate waveform for TTS
            )
            audio_track.clips.append(clip)
            
            self.timeline_widget.refresh_tracks()
