from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTextEdit, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt


class CaptionDialog(QDialog):
    """Dialog for configuring auto caption settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 Auto Caption Settings")
        self.setFixedSize(400, 200)
        self.result_language = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Language Selection
        lang_group = QGroupBox("Ngôn ngữ trong video")
        lang_layout = QHBoxLayout(lang_group)
        
        lang_layout.addWidget(QLabel("Ngôn ngữ:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems([
            "🔄 Tự động phát hiện",
            "🇻🇳 Tiếng Việt",
            "🇺🇸 English",
            "🇨🇳 中文 (Chinese)",
            "🇯🇵 日本語 (Japanese)",
            "🇰🇷 한국어 (Korean)",
        ])
        self.lang_combo.setMinimumWidth(200)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        
        layout.addWidget(lang_group)
        
        # Info label
        info = QLabel("💡 Whisper AI sẽ transcribe audio thành text và tạo subtitles trên timeline.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        start_btn = QPushButton("🚀 Bắt đầu")
        start_btn.setStyleSheet("background-color: #6366f1; color: white; font-weight: bold;")
        start_btn.clicked.connect(self.accept_with_settings)
        btn_layout.addWidget(start_btn)
        
        layout.addLayout(btn_layout)
    
    def accept_with_settings(self):
        # Map combo selection to language code
        lang_map = {
            0: None,    # Auto-detect
            1: "vi",    # Vietnamese
            2: "en",    # English
            3: "zh",    # Chinese
            4: "ja",    # Japanese
            5: "ko",    # Korean
        }
        self.result_language = lang_map.get(self.lang_combo.currentIndex())
        self.accept()
    
    def get_language(self):
        return self.result_language


class TTSDialog(QDialog):
    """Dialog for Text-to-Speech with voice selection."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎤 Text to Speech")
        self.setFixedSize(500, 350)
        self.result_text = None
        self.result_voice = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Voice Selection
        voice_group = QGroupBox("Chọn giọng nói")
        voice_layout = QHBoxLayout(voice_group)
        
        voice_layout.addWidget(QLabel("Giọng:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "🇻🇳 Hoài My (Nữ - Việt Nam)",
            "🇻🇳 Nam Minh (Nam - Việt Nam)",
            "🇺🇸 Aria (Nữ - US English)",
            "🇺🇸 Guy (Nam - US English)",
            "🇬🇧 Sonia (Nữ - UK English)",
            "🇨🇳 Xiaoxiao (Nữ - Chinese)",
            "🇯🇵 Nanami (Nữ - Japanese)",
            "🇰🇷 SunHi (Nữ - Korean)",
        ])
        self.voice_combo.setMinimumWidth(250)
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch()
        
        layout.addWidget(voice_group)
        
        # Text Input
        text_group = QGroupBox("Nhập văn bản")
        text_layout = QVBoxLayout(text_group)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Nhập văn bản cần chuyển thành giọng nói...")
        self.text_edit.setMinimumHeight(120)
        text_layout.addWidget(self.text_edit)
        
        layout.addWidget(text_group)
        
        # Info
        info = QLabel("💡 Sử dụng Microsoft Edge TTS - chất lượng cao, miễn phí")
        info.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        layout.addWidget(info)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        generate_btn = QPushButton("🔊 Tạo audio")
        generate_btn.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold;")
        generate_btn.clicked.connect(self.accept_with_settings)
        btn_layout.addWidget(generate_btn)
        
        layout.addLayout(btn_layout)
    
    def accept_with_settings(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            return
        
        # Map combo selection to voice name
        voice_map = {
            0: "vi-VN-HoaiMyNeural",
            1: "vi-VN-NamMinhNeural",
            2: "en-US-AriaNeural",
            3: "en-US-GuyNeural",
            4: "en-GB-SoniaNeural",
            5: "zh-CN-XiaoxiaoNeural",
            6: "ja-JP-NanamiNeural",
            7: "ko-KR-SunHiNeural",
        }
        
        self.result_text = text
        self.result_voice = voice_map.get(self.voice_combo.currentIndex(), "vi-VN-HoaiMyNeural")
        self.accept()
    
    def get_text(self):
        return self.result_text
    
    def get_voice(self):
        return self.result_voice
