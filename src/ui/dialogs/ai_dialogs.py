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
        self.setFixedSize(450, 280)
        self.result_language = None
        self.result_translate_to = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Mode Selection
        mode_group = QGroupBox("Chế độ")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "📝 Transcribe (Giữ nguyên ngôn ngữ gốc)",
            "🌐 Translate (Dịch sang ngôn ngữ khác)",
        ])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        
        layout.addWidget(mode_group)
        
        # Language Selection (for transcribe mode)
        self.source_group = QGroupBox("Ngôn ngữ trong video")
        source_layout = QHBoxLayout(self.source_group)
        
        source_layout.addWidget(QLabel("Ngôn ngữ:"))
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems([
            "🔄 Tự động phát hiện",
            "🇻🇳 Tiếng Việt",
            "🇺🇸 English",
            "🇨🇳 中文 (Chinese)",
            "🇯🇵 日本語 (Japanese)",
            "🇰🇷 한국어 (Korean)",
        ])
        self.source_lang_combo.setMinimumWidth(200)
        source_layout.addWidget(self.source_lang_combo)
        source_layout.addStretch()
        
        layout.addWidget(self.source_group)
        
        # Target Language (for translate mode)
        self.target_group = QGroupBox("Dịch sang ngôn ngữ")
        target_layout = QHBoxLayout(self.target_group)
        
        target_layout.addWidget(QLabel("Dịch sang:"))
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems([
            "🇻🇳 Tiếng Việt",
            "🇺🇸 English",
            "🇨🇳 中文 (Chinese)",
            "🇯🇵 日本語 (Japanese)",
            "🇰🇷 한국어 (Korean)",
            "🇫🇷 Français",
            "🇩🇪 Deutsch",
            "🇪🇸 Español",
        ])
        self.target_lang_combo.setMinimumWidth(200)
        target_layout.addWidget(self.target_lang_combo)
        target_layout.addStretch()
        
        self.target_group.hide()  # Hidden by default
        layout.addWidget(self.target_group)
        
        # Info label
        self.info_label = QLabel("💡 Whisper AI sẽ transcribe audio thành text và tạo subtitles trên timeline.")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        layout.addWidget(self.info_label)
        
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
    
    def on_mode_changed(self, index):
        if index == 0:  # Transcribe mode
            self.source_group.show()
            self.target_group.hide()
            self.info_label.setText("💡 Whisper AI sẽ transcribe audio thành text và tạo subtitles trên timeline.")
        else:  # Translate mode
            self.source_group.hide()
            self.target_group.show()
            self.info_label.setText("💡 Whisper AI sẽ transcribe audio rồi dịch sang ngôn ngữ đã chọn.")
    
    def accept_with_settings(self):
        # Map combo selection to language code
        source_lang_map = {
            0: None, 1: "vi", 2: "en", 3: "zh", 4: "ja", 5: "ko",
        }
        target_lang_map = {
            0: "vi", 1: "en", 2: "zh", 3: "ja", 4: "ko", 5: "fr", 6: "de", 7: "es",
        }
        
        if self.mode_combo.currentIndex() == 0:  # Transcribe
            self.result_language = source_lang_map.get(self.source_lang_combo.currentIndex())
            self.result_translate_to = None
        else:  # Translate
            self.result_language = None
            self.result_translate_to = target_lang_map.get(self.target_lang_combo.currentIndex())
        
        self.accept()
    
    def get_language(self):
        return self.result_language
    
    def get_translate_to(self):
        return self.result_translate_to


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
