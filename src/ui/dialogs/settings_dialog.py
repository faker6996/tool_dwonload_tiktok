"""
Settings dialog for managing API keys and application configuration.
"""
import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QGroupBox, QCheckBox,
    QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt


CONFIG_PATH = os.path.expanduser("~/.tiktok_downloader_config.json")


class SettingsDialog(QDialog):
    """Settings dialog with API keys and configuration tabs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Settings")
        self.setFixedSize(550, 450)
        self.config = self._load_config()
        self.setup_ui()
    
    def _load_config(self) -> dict:
        """Load config from file."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {}
    
    def _save_config(self):
        """Save config to file."""
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget
        tabs = QTabWidget()
        
        # API Keys Tab
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)
        
        # Gemini API Key
        gemini_group = QGroupBox("🤖 Gemini Pro")
        gemini_layout = QVBoxLayout(gemini_group)
        
        gemini_row = QHBoxLayout()
        gemini_row.addWidget(QLabel("API Key:"))
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setPlaceholderText("Nhập Gemini API Key...")
        self.gemini_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key_input.setText(self.config.get("gemini_api_key", ""))
        gemini_row.addWidget(self.gemini_key_input)
        gemini_layout.addLayout(gemini_row)
        
        gemini_info = QLabel("💡 Lấy API key từ: https://aistudio.google.com")
        gemini_info.setStyleSheet("color: #6b7280; font-size: 10px;")
        gemini_layout.addWidget(gemini_info)
        
        api_layout.addWidget(gemini_group)
        
        # OpenAI API Key
        openai_group = QGroupBox("🧠 OpenAI (GPT-5)")
        openai_layout = QVBoxLayout(openai_group)
        
        openai_row = QHBoxLayout()
        openai_row.addWidget(QLabel("API Key:"))
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setPlaceholderText("Nhập OpenAI API Key...")
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setText(self.config.get("openai_api_key", ""))
        openai_row.addWidget(self.openai_key_input)
        openai_layout.addLayout(openai_row)
        
        openai_info = QLabel("💡 Lấy API key từ: https://platform.openai.com")
        openai_info.setStyleSheet("color: #6b7280; font-size: 10px;")
        openai_layout.addWidget(openai_info)
        
        api_layout.addWidget(openai_group)
        api_layout.addStretch()
        
        tabs.addTab(api_tab, "🔑 API Keys")
        
        # General Settings Tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Translation Settings
        trans_group = QGroupBox("🌐 Dịch thuật")
        trans_layout = QVBoxLayout(trans_group)
        
        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("Provider mặc định:"))
        self.default_provider_combo = QComboBox()
        self.default_provider_combo.addItems([
            "Google Translate (Miễn phí)",
            "Gemini Pro",
            "GPT-5",
            "GPT-5 mini (Rẻ nhất 🔥)",
        ])
        current_provider = self.config.get("default_translation_provider", 0)
        self.default_provider_combo.setCurrentIndex(current_provider)
        provider_row.addWidget(self.default_provider_combo)
        trans_layout.addLayout(provider_row)
        
        general_layout.addWidget(trans_group)
        
        # Whisper Settings
        whisper_group = QGroupBox("🎯 Whisper (Transcription)")
        whisper_layout = QVBoxLayout(whisper_group)
        
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems([
            "tiny (Nhanh, kém chính xác)",
            "base (Cân bằng ✅)",
            "small (Chậm, chính xác hơn)",
            "medium (Rất chậm, rất chính xác)",
        ])
        current_model = self.config.get("whisper_model", 1)
        self.whisper_model_combo.setCurrentIndex(current_model)
        model_row.addWidget(self.whisper_model_combo)
        whisper_layout.addLayout(model_row)
        
        general_layout.addWidget(whisper_group)
        
        # Download Settings
        download_group = QGroupBox("📥 Download")
        download_layout = QVBoxLayout(download_group)
        
        self.auto_translate_title = QCheckBox("Tự động dịch tiêu đề sang Tiếng Việt")
        self.auto_translate_title.setChecked(self.config.get("auto_translate_title", True))
        download_layout.addWidget(self.auto_translate_title)
        
        general_layout.addWidget(download_group)
        general_layout.addStretch()
        
        tabs.addTab(general_tab, "⚙️ Cài đặt chung")
        
        layout.addWidget(tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Lưu")
        save_btn.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def save_settings(self):
        """Save all settings."""
        # API Keys
        self.config["gemini_api_key"] = self.gemini_key_input.text().strip()
        self.config["openai_api_key"] = self.openai_key_input.text().strip()
        
        # General settings
        self.config["default_translation_provider"] = self.default_provider_combo.currentIndex()
        self.config["whisper_model"] = self.whisper_model_combo.currentIndex()
        self.config["auto_translate_title"] = self.auto_translate_title.isChecked()
        
        # Apply API keys to services
        self._apply_api_keys()
        
        # Save to file
        self._save_config()
        
        QMessageBox.information(self, "Settings", "✅ Đã lưu cài đặt!")
        self.accept()
    
    def _apply_api_keys(self):
        """Apply API keys to translation service."""
        from src.core.ai.translation import translation_service
        
        gemini_key = self.config.get("gemini_api_key", "")
        openai_key = self.config.get("openai_api_key", "")
        
        if gemini_key:
            translation_service.set_gemini_api_key(gemini_key)
        if openai_key:
            translation_service.set_openai_api_key(openai_key)
        
        # Set default provider
        provider_map = {0: "google", 1: "gemini", 2: "gpt5", 3: "gpt5_mini"}
        provider = provider_map.get(self.config.get("default_translation_provider", 0), "google")
        translation_service.set_provider(provider)


def load_settings_on_startup():
    """Load and apply settings when app starts."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            
            from src.core.ai.translation import translation_service
            
            gemini_key = config.get("gemini_api_key", "")
            openai_key = config.get("openai_api_key", "")
            
            if gemini_key:
                translation_service.set_gemini_api_key(gemini_key)
            if openai_key:
                translation_service.set_openai_api_key(openai_key)
            
            # Set default provider
            provider_map = {0: "google", 1: "gemini", 2: "gpt5", 3: "gpt5_mini"}
            provider = provider_map.get(config.get("default_translation_provider", 0), "google")
            translation_service.set_provider(provider)
            
            print("✅ Settings loaded from config")
    except Exception as e:
        print(f"⚠️ Error loading settings: {e}")
