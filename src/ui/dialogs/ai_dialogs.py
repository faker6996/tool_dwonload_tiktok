from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTextEdit, QProgressBar, QGroupBox, QLineEdit
)
from PyQt6.QtCore import Qt


class CaptionDialog(QDialog):
    """Dialog for configuring auto caption settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 Auto Sub Settings")
        self.setFixedSize(500, 480)  # Larger for more options
        self.result_language = None
        self.result_translate_to = None
        self.result_mode = "transcribe"  # transcribe, translate, or remove
        self.result_remove_settings = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Mode Selection
        mode_group = QGroupBox("Chế độ")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "📝 Transcribe (Tạo sub từ audio)",
            "🌐 Translate (Dịch sub sang ngôn ngữ khác)",
            "👁️ OCR Extract (Đọc sub từ video - không cần audio)",
        ])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        
        # Remove Sub checkbox option
        from PyQt6.QtWidgets import QCheckBox
        self.remove_sub_checkbox = QCheckBox("🗑️ Xoá sub gốc trước khi thêm sub mới")
        self.remove_sub_checkbox.setToolTip("Xoá hardcoded subtitles trong video trước")
        self.remove_sub_checkbox.stateChanged.connect(self.on_remove_sub_changed)
        mode_layout.addWidget(self.remove_sub_checkbox)
        
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
        
        # Translation Provider Selection (only for translate mode)
        self.provider_group = QGroupBox("🤖 Công cụ dịch")
        provider_layout = QVBoxLayout(self.provider_group)
        
        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            "Google Translate (Miễn phí)",
            "Gemini Pro",
            "GPT-5 (Chất lượng cao)",
            "GPT-5 mini",
            "GPT-5 nano (Rẻ nhất 🔥)",
        ])
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        self.provider_combo.setMinimumWidth(200)
        provider_row.addWidget(self.provider_combo)
        provider_row.addStretch()
        provider_layout.addLayout(provider_row)
        
        # API Key input (for Gemini)
        self.api_key_row = QHBoxLayout()
        self.api_key_row.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Nhập Gemini API Key...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_row.addWidget(self.api_key_input)
        provider_layout.addLayout(self.api_key_row)
        
        # Hide API key row initially
        self.api_key_input.hide()
        
        self.provider_group.hide()  # Hidden by default
        layout.addWidget(self.provider_group)
        
        # Whisper Provider Selection (Local vs OpenAI API)
        self.whisper_group = QGroupBox("🎯 Whisper Engine")
        whisper_layout = QVBoxLayout(self.whisper_group)
        
        whisper_row = QHBoxLayout()
        whisper_row.addWidget(QLabel("Engine:"))
        self.whisper_engine_combo = QComboBox()
        self.whisper_engine_combo.addItems([
            "💻 Local (MLX/CPU - Miễn phí)",
            "☁️ OpenAI API (Nhanh, $0.006/phút)",
        ])
        self.whisper_engine_combo.currentIndexChanged.connect(self.on_whisper_engine_changed)
        whisper_row.addWidget(self.whisper_engine_combo)
        whisper_row.addStretch()
        whisper_layout.addLayout(whisper_row)
        
        # OpenAI API key for Whisper (reuse from settings if available)
        self.whisper_api_row = QHBoxLayout()
        self.whisper_api_row.addWidget(QLabel("API Key:"))
        self.whisper_api_input = QLineEdit()
        self.whisper_api_input.setPlaceholderText("Nhập OpenAI API Key...")
        self.whisper_api_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Pre-fill from config if available
        self._load_saved_whisper_key()
        
        self.whisper_api_row.addWidget(self.whisper_api_input)
        whisper_layout.addLayout(self.whisper_api_row)
        self.whisper_api_input.hide()  # Hidden by default (Local mode)
        
        layout.addWidget(self.whisper_group)
        
        # Remove Sub Settings Group (hidden by default)
        self.remove_group = QGroupBox("🗑️ Cài đặt xoá subtitle")
        remove_layout = QVBoxLayout(self.remove_group)
        
        # Algorithm selection
        algo_row = QHBoxLayout()
        algo_row.addWidget(QLabel("Phương pháp:"))
        self.remove_algo_combo = QComboBox()
        self.remove_algo_combo.addItems([
            "🌫️ Blur (Nhanh ⚡)",
            "⬛ Black (Nhanh ⚡)",
            "✂️ Crop (Nhanh ⚡)",
            "🎨 AI Inpaint (Chậm 🐢)",
        ])
        algo_row.addWidget(self.remove_algo_combo)
        algo_row.addStretch()
        remove_layout.addLayout(algo_row)
        
        # Height slider
        height_row = QHBoxLayout()
        height_row.addWidget(QLabel("Vùng sub (%):"))
        from PyQt6.QtWidgets import QSlider
        self.remove_height_slider = QSlider(Qt.Orientation.Horizontal)
        self.remove_height_slider.setMinimum(5)
        self.remove_height_slider.setMaximum(40)
        self.remove_height_slider.setValue(15)
        self.remove_height_slider.valueChanged.connect(
            lambda v: self.remove_height_label.setText(f"{v}%")
        )
        height_row.addWidget(self.remove_height_slider)
        self.remove_height_label = QLabel("15%")
        height_row.addWidget(self.remove_height_label)
        remove_layout.addLayout(height_row)
        
        self.remove_group.hide()  # Hidden by default
        layout.addWidget(self.remove_group)
        
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
            self.provider_group.hide()
            # Hide remove sub option in transcribe mode
            self.remove_sub_checkbox.hide()
            self.remove_group.hide()
            self.info_label.setText("💡 Whisper AI sẽ transcribe audio thành text và tạo subtitles trên timeline.")
            self.info_label.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        elif index == 1:  # Translate mode
            self.source_group.hide()
            self.target_group.show()
            self.provider_group.show()
            # Show remove sub option in translate mode
            self.remove_sub_checkbox.show()
            self.info_label.setText("💡 Whisper AI sẽ transcribe audio rồi dịch sang ngôn ngữ đã chọn.")
            self.info_label.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        else:  # OCR Extract mode (index == 2)
            self.source_group.hide()
            self.target_group.show()  # Show target language for translation
            self.provider_group.show()
            self.remove_sub_checkbox.show()
            self.remove_sub_checkbox.setChecked(True)  # Default: remove sub first
            self.info_label.setText("👁️ OCR sẽ đọc text từ video frame và dịch. Không cần audio!")
            self.info_label.setStyleSheet("color: #22c55e; font-size: 11px;")
        
        # Keep remove_group visibility based on checkbox
        self.remove_group.setVisible(self.remove_sub_checkbox.isChecked() and index >= 1)
    
    def on_remove_sub_changed(self, state):
        """Show/hide remove settings when checkbox is toggled."""
        self.remove_group.setVisible(state == 2)  # Qt.CheckState.Checked = 2
        if state == 2:
            self.info_label.setText("⚠️ Sẽ xoá sub gốc trước khi thêm sub mới. Video mới sẽ được tạo.")
            self.info_label.setStyleSheet("color: #f59e0b; font-size: 11px;")
    
    def on_provider_changed(self, index):
        # Show API key input for providers that need it (Gemini, GPT-5, GPT-5 mini)
        if index >= 1:  # Not Google Translate
            self.api_key_input.show()
            if index == 1:
                self.api_key_input.setPlaceholderText("Nhập Gemini API Key...")
            else:
                self.api_key_input.setPlaceholderText("Nhập OpenAI API Key...")
        else:
            self.api_key_input.hide()
    
    def on_whisper_engine_changed(self, index):
        """Show/hide OpenAI API key input based on Whisper engine selection."""
        if index == 1:  # OpenAI API
            self.whisper_api_input.show()
        else:
            self.whisper_api_input.hide()
    
    def _load_saved_whisper_key(self):
        """Load OpenAI API key from saved config."""
        import os
        import json
        config_path = os.path.expanduser("~/.tiktok_downloader_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    api_key = config.get("openai_api_key", "")
                    if api_key:
                        self.whisper_api_input.setText(api_key)
        except:
            pass
    
    def accept_with_settings(self):
        mode_index = self.mode_combo.currentIndex()
        
        # Configure Whisper engine (Local vs OpenAI API)
        whisper_engine = self.whisper_engine_combo.currentIndex()
        self.result_use_openai_whisper = (whisper_engine == 1)
        
        if self.result_use_openai_whisper:
            from src.core.ai.transcription import transcription_service
            api_key = self.whisper_api_input.text().strip()
            if api_key:
                transcription_service.set_openai_api_key(api_key)
                transcription_service.set_use_openai_api(True)
            else:
                # No API key, fallback to local
                self.result_use_openai_whisper = False
                transcription_service.set_use_openai_api(False)
        else:
            from src.core.ai.transcription import transcription_service
            transcription_service.set_use_openai_api(False)
        
        # Configure translation provider for translate mode
        if mode_index == 1:  # Translate mode
            from src.core.ai.translation import translation_service
            
            provider_map = {0: "google", 1: "gemini", 2: "gpt5", 3: "gpt5_mini", 4: "gpt5_nano"}
            provider = provider_map.get(self.provider_combo.currentIndex(), "google")
            translation_service.set_provider(provider)
            
            # Set API key if provided
            api_key = self.api_key_input.text().strip()
            if api_key:
                if provider == "gemini":
                    translation_service.set_gemini_api_key(api_key)
                elif provider in ["gpt5", "gpt5_mini", "gpt5_nano"]:
                    translation_service.set_openai_api_key(api_key)
        
        # Map combo selection to language code
        source_lang_map = {
            0: None, 1: "vi", 2: "en", 3: "zh", 4: "ja", 5: "ko",
        }
        target_lang_map = {
            0: "vi", 1: "en", 2: "zh", 3: "ja", 4: "ko", 5: "fr", 6: "de", 7: "es",
        }
        
        if mode_index == 0:  # Transcribe
            self.result_mode = "transcribe"
            self.result_language = source_lang_map.get(self.source_lang_combo.currentIndex())
            self.result_translate_to = None
        elif mode_index == 1:  # Translate
            self.result_mode = "translate"
            self.result_language = None
            self.result_translate_to = target_lang_map.get(self.target_lang_combo.currentIndex())
        else:  # OCR Extract (mode_index == 2)
            self.result_mode = "ocr"
            self.result_language = None
            self.result_translate_to = target_lang_map.get(self.target_lang_combo.currentIndex())
        
        # Handle remove sub option (checkbox)
        if self.remove_sub_checkbox.isChecked():
            algo_map = {0: "blur", 1: "black", 2: "crop", 3: "inpaint"}
            self.result_remove_settings = {
                "algorithm": algo_map.get(self.remove_algo_combo.currentIndex(), "blur"),
                "bottom_percent": self.remove_height_slider.value() / 100.0,
            }
        else:
            self.result_remove_settings = None
        
        self.accept()
    
    def get_mode(self):
        return self.result_mode
    
    def get_language(self):
        return self.result_language
    
    def get_translate_to(self):
        return self.result_translate_to
    
    def get_remove_settings(self):
        return self.result_remove_settings
    
    def get_use_openai_whisper(self) -> bool:
        """Return whether user selected OpenAI Whisper API."""
        return getattr(self, 'result_use_openai_whisper', False)


class TTSDialog(QDialog):
    """Dialog for Text-to-Speech with voice selection."""
    
    def __init__(self, parent=None, initial_text: str = ""):
        super().__init__(parent)
        self.setWindowTitle("🎤 Text to Speech")
        self.setFixedSize(500, 450)  # Slightly taller for new checkbox
        self.result_text = None
        self.result_voice = None
        self.result_sync_subtitles = False  # Whether to sync back to subtitles
        self._initial_text = initial_text
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
        self.text_edit.setMinimumHeight(150)
        
        # Pre-fill with subtitle text if available
        if self._initial_text:
            self.text_edit.setText(self._initial_text)
        
        text_layout.addWidget(self.text_edit)
        
        layout.addWidget(text_group)
        
        # Sync subtitles checkbox - only show if there's initial text (from subtitles)
        from PyQt6.QtWidgets import QCheckBox
        self.sync_checkbox = QCheckBox("📝 Cập nhật cả subtitle trên timeline")
        self.sync_checkbox.setToolTip("Khi bật, text đã chỉnh sửa sẽ được cập nhật lại vào subtitle track")
        self.sync_checkbox.setChecked(True)  # Default: sync back
        if self._initial_text:
            layout.addWidget(self.sync_checkbox)
        else:
            self.sync_checkbox.hide()
        
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
        self.result_sync_subtitles = self.sync_checkbox.isChecked() if self._initial_text else False
        self.accept()
    
    def get_text(self):
        return self.result_text
    
    def get_voice(self):
        return self.result_voice
    
    def should_sync_subtitles(self) -> bool:
        """Return whether user wants to sync edited text back to subtitles."""
        return self.result_sync_subtitles
