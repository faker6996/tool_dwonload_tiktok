"""
Dialog for configuring subtitle removal settings.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QGroupBox, QSpinBox, QSlider, QCheckBox
)
from PyQt6.QtCore import Qt


class SubtitleRemovalDialog(QDialog):
    """Dialog for configuring subtitle removal settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🗑️ Remove Subtitles")
        self.setFixedSize(450, 350)
        self.result_settings = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Detection Mode
        mode_group = QGroupBox("Chế độ phát hiện")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "🔍 Tự động (Bottom 15%)",
            "📐 Tùy chỉnh vùng",
        ])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        
        layout.addWidget(mode_group)
        
        # Region Settings (custom mode)
        self.region_group = QGroupBox("Vùng subtitle (% từ đáy)")
        region_layout = QHBoxLayout(self.region_group)
        
        region_layout.addWidget(QLabel("Chiều cao:"))
        self.height_slider = QSlider(Qt.Orientation.Horizontal)
        self.height_slider.setMinimum(5)
        self.height_slider.setMaximum(40)
        self.height_slider.setValue(15)
        self.height_slider.valueChanged.connect(self.on_slider_changed)
        region_layout.addWidget(self.height_slider)
        
        self.height_label = QLabel("15%")
        self.height_label.setMinimumWidth(40)
        region_layout.addWidget(self.height_label)
        
        self.region_group.hide()
        layout.addWidget(self.region_group)
        
        # Algorithm
        algo_group = QGroupBox("Phương pháp xoá")
        algo_layout = QVBoxLayout(algo_group)
        
        self.algo_combo = QComboBox()
        self.algo_combo.addItems([
            "🌫️ Blur (FFmpeg - Nhanh ⚡)",
            "⬛ Black out (FFmpeg - Nhanh ⚡)",
            "✂️ Crop (FFmpeg - Nhanh ⚡, cắt bỏ)",
            "🎨 AI Inpaint (OpenCV - Chậm 🐢, chất lượng cao)",
        ])
        self.algo_combo.currentIndexChanged.connect(self.on_algo_changed)
        algo_layout.addWidget(self.algo_combo)
        
        layout.addWidget(algo_group)
        
        # Options
        self.keep_audio = QCheckBox("🔊 Giữ nguyên audio")
        self.keep_audio.setChecked(True)
        layout.addWidget(self.keep_audio)
        
        # Info label (dynamic)
        self.info_label = QLabel("⚡ FFmpeg Blur: Nhanh (~1-2 phút), làm mờ vùng subtitle.")
        self.info_label.setStyleSheet("color: #22c55e; font-size: 11px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        start_btn = QPushButton("🚀 Xoá Subtitle")
        start_btn.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold;")
        start_btn.clicked.connect(self.accept_with_settings)
        btn_layout.addWidget(start_btn)
        
        layout.addLayout(btn_layout)
    
    def on_mode_changed(self, index):
        self.region_group.setVisible(index == 1)
    
    def on_slider_changed(self, value):
        self.height_label.setText(f"{value}%")
    
    def on_algo_changed(self, index):
        """Update info label based on selected algorithm."""
        info_texts = [
            ("⚡ FFmpeg Blur: Nhanh (~1-2 phút), làm mờ vùng subtitle.", "#22c55e"),
            ("⚡ FFmpeg Black: Nhanh (~1-2 phút), xoá thành màu đen.", "#22c55e"),
            ("⚡ FFmpeg Crop: Nhanh (~1-2 phút), cắt bỏ phần dưới video.", "#f59e0b"),
            ("🐢 AI Inpaint: Chậm (~30+ phút), fill background thông minh.", "#ef4444"),
        ]
        text, color = info_texts[index] if index < len(info_texts) else info_texts[0]
        self.info_label.setText(text)
        self.info_label.setStyleSheet(f"color: {color}; font-size: 11px;")
    
    def accept_with_settings(self):
        # Map: 0=blur, 1=black, 2=crop, 3=inpaint
        algorithm_map = {0: "blur", 1: "black", 2: "crop", 3: "inpaint"}
        
        self.result_settings = {
            "auto_detect": self.mode_combo.currentIndex() == 0,
            "bottom_percent": self.height_slider.value() / 100.0,
            "algorithm": algorithm_map.get(self.algo_combo.currentIndex(), "blur"),
            "keep_audio": self.keep_audio.isChecked(),
        }
        self.accept()
    
    def get_settings(self):
        return self.result_settings
