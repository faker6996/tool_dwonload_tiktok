from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QMovie
import time


class AIProgressDialog(QDialog):
    """Progress dialog for AI operations like transcription and TTS."""
    
    def __init__(self, parent=None, title="Processing...", message="Please wait..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(450, 180)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        
        self.setup_ui(message)
    
    def setup_ui(self, message):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Icon and title
        title_layout = QHBoxLayout()
        icon_label = QLabel("⏳")
        icon_label.setStyleSheet("font-size: 32px;")
        title_layout.addWidget(icon_label)
        
        self.title_label = QLabel(message)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e0e0;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate mode
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #27272a;
                border-radius: 5px;
                background-color: #18181b;
                height: 20px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Time elapsed
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #71717a; font-size: 11px;")
        layout.addWidget(self.time_label)
        
        layout.addStretch()
    
    def set_status(self, status: str):
        self.status_label.setText(status)
    
    def set_progress(self, value: int, maximum: int = 100):
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
    
    def set_indeterminate(self):
        self.progress_bar.setMaximum(0)
    
    def set_complete(self, success: bool = True):
        if success:
            self.title_label.setText("✅ Hoàn thành!")
            self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #22c55e;")
        else:
            self.title_label.setText("❌ Lỗi!")
            self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ef4444;")
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100 if success else 0)


class TranscriptionWorker(QThread):
    """Worker thread for transcription to avoid blocking UI."""
    progress = pyqtSignal(str)  # Status message
    finished = pyqtSignal(list)  # Segments result
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, file_path: str, language: str = None, translate_to: str = None):
        super().__init__()
        self.file_path = file_path
        self.language = language
        self.translate_to = translate_to
    
    def run(self):
        try:
            from src.core.ai.transcription import transcription_service
            
            if self.translate_to:
                self.progress.emit(f"🎯 Đang transcribe và dịch sang {self.translate_to}...")
                segments = transcription_service.transcribe_and_translate(
                    self.file_path, 
                    target_language=self.translate_to
                )
            else:
                self.progress.emit(f"🎯 Đang transcribe ({self.language or 'auto-detect'})...")
                segments = transcription_service.transcribe(
                    self.file_path, 
                    language=self.language
                )
            
            self.finished.emit(segments)
            
        except Exception as e:
            self.error.emit(str(e))


class TTSWorker(QThread):
    """Worker thread for TTS to avoid blocking UI."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, float)  # output_path, duration
    error = pyqtSignal(str)
    
    def __init__(self, text: str, output_path: str, voice: str):
        super().__init__()
        self.text = text
        self.output_path = output_path
        self.voice = voice
    
    def run(self):
        try:
            from src.core.ai.tts import tts_service
            
            self.progress.emit(f"🎤 Đang tạo giọng nói...")
            tts_service.generate_speech(self.text, self.output_path, voice=self.voice)
            
            # Get duration
            try:
                from mutagen.mp3 import MP3
                audio = MP3(self.output_path)
                duration = audio.info.length
            except:
                words = len(self.text.split())
                duration = max(1.0, words * 0.4)
            
            self.finished.emit(self.output_path, duration)
            
        except Exception as e:
            self.error.emit(str(e))
