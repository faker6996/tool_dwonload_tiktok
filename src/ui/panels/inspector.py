from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QWidget, QGridLayout, 
                             QSpinBox, QDoubleSpinBox, QSlider, QComboBox, QHBoxLayout, QScrollArea, QAbstractSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal

class Inspector(QFrame):
    clip_changed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self.setMinimumWidth(300)
        self.current_clip = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title
        title = QLabel("Inspector")
        title.setObjectName("panel_title")
        main_layout.addWidget(title)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(24)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. TRANSFORM Section
        self.create_section_header("TRANSFORM")
        
        # Position
        pos_layout = QGridLayout()
        pos_layout.setSpacing(10)
        
        self.pos_x = self.create_spinbox("Position X", -1920, 1920, 0)
        self.pos_y = self.create_spinbox("Position Y", -1080, 1080, 0)
        
        pos_layout.addWidget(QLabel("Position X"), 0, 0)
        pos_layout.addWidget(QLabel("Position Y"), 0, 1)
        pos_layout.addWidget(self.pos_x, 1, 0)
        pos_layout.addWidget(self.pos_y, 1, 1)
        
        self.content_layout.addLayout(pos_layout)

        # Scale
        scale_container, self.scale_slider, self.scale_spin = self.create_slider_input("Scale", 1, 500, 100, "%")
        self.content_layout.addWidget(scale_container)

        # Rotation
        rotation_container, self.rotation_slider, self.rotation_spin = self.create_slider_input("Rotation", -360, 360, 0, "°")
        self.content_layout.addWidget(rotation_container)

        self.add_separator()

        # 2. OPACITY Section
        self.create_section_header("OPACITY")
        
        opacity_container, self.opacity_slider, self.opacity_spin = self.create_slider_input("Opacity", 0, 100, 100, "%")
        self.content_layout.addWidget(opacity_container)
        
        # Blend Mode
        blend_layout = QVBoxLayout()
        blend_layout.setSpacing(8)
        blend_label = QLabel("Blend Mode")
        blend_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        self.blend_combo = QComboBox()
        self.blend_combo.addItems(["Normal", "Multiply", "Screen", "Overlay", "Darken", "Lighten"])
        self.blend_combo.currentTextChanged.connect(self.update_clip_transform)
        blend_layout.addWidget(blend_label)
        blend_layout.addWidget(self.blend_combo)
        self.content_layout.addLayout(blend_layout)

        self.add_separator()

        # 3. AUDIO Section
        self.create_section_header("AUDIO")
        
        volume_container, self.volume_slider, self.volume_spin = self.create_slider_input("Volume", 0, 200, 100, "%")
        self.content_layout.addWidget(volume_container)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Connect Signals
        self.pos_x.valueChanged.connect(self.update_clip_transform)
        self.pos_y.valueChanged.connect(self.update_clip_transform)

    def create_section_header(self, text):
        header = QHBoxLayout()
        label = QLabel(text)
        label.setStyleSheet("font-weight: 600; color: #a1a1aa; font-size: 11px; letter-spacing: 0.5px;")
        header.addWidget(label)
        header.addStretch()
        self.content_layout.addLayout(header)

    def create_spinbox(self, tooltip, min_val, max_val, default):
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setToolTip(tooltip)
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        return spin

    def create_slider_input(self, label_text, min_val, max_val, default, suffix=""):
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #a1a1aa;")
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setSuffix(suffix)
        spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        spin.setFixedWidth(60)
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Sync
        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)
        
        # Connect to update handler
        slider.valueChanged.connect(self.update_clip_transform)

        layout.addWidget(label, 0, 0)
        layout.addWidget(spin, 0, 1)
        layout.addWidget(slider, 1, 0, 1, 2)
        
        return container, slider, spin

    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #27272a; margin: 8px 0;")
        self.content_layout.addWidget(line)

    def set_clip(self, clip):
        self.current_clip = clip
        self.setEnabled(clip is not None)
        
        if not clip:
            return

        # Block signals to prevent feedback loop
        self.block_signals(True)
        
        # Update UI from Clip Data
        # Using safe access with defaults
        self.pos_x.setValue(getattr(clip, 'position_x', 0))
        self.pos_y.setValue(getattr(clip, 'position_y', 0))
        self.scale_slider.setValue(int(getattr(clip, 'scale_x', 1.0) * 100))
        self.rotation_slider.setValue(int(getattr(clip, 'rotation', 0)))
        
        self.opacity_slider.setValue(int(getattr(clip, 'opacity', 1.0) * 100))
        self.blend_combo.setCurrentText(getattr(clip, 'blend_mode', 'Normal'))
        
        self.volume_slider.setValue(int(getattr(clip, 'volume', 1.0) * 100))
        
        self.block_signals(False)

    def update_clip_transform(self):
        if not self.current_clip:
            return
            
        # Update Clip Data from UI
        self.current_clip.position_x = self.pos_x.value()
        self.current_clip.position_y = self.pos_y.value()
        self.current_clip.scale_x = self.scale_slider.value() / 100.0
        self.current_clip.scale_y = self.scale_slider.value() / 100.0 # Uniform scale for now
        self.current_clip.rotation = self.rotation_slider.value()
        
        self.current_clip.opacity = self.opacity_slider.value() / 100.0
        self.current_clip.blend_mode = self.blend_combo.currentText()
        
        self.current_clip.volume = self.volume_slider.value() / 100.0
        
        # Emit signal
        self.clip_changed.emit(self.current_clip)

    def block_signals(self, block):
        self.pos_x.blockSignals(block)
        self.pos_y.blockSignals(block)
        self.scale_slider.blockSignals(block)
        self.scale_spin.blockSignals(block)
        self.rotation_slider.blockSignals(block)
        self.rotation_spin.blockSignals(block)
        self.opacity_slider.blockSignals(block)
        self.opacity_spin.blockSignals(block)
        self.blend_combo.blockSignals(block)
        self.volume_slider.blockSignals(block)
        self.volume_spin.blockSignals(block)
