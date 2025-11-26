from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QWidget, QGridLayout, 
                             QDoubleSpinBox, QSlider, QComboBox, QScrollArea, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from src.core.timeline.clip import Clip

class Inspector(QFrame):
    clip_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self.setMinimumWidth(320) # Ensure enough space for controls
        self.current_clip = None
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        title = QLabel("Inspector")
        title.setObjectName("panel_title")
        layout.addWidget(title)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
        # Transform Section
        self.add_section_header("Transform")
        
        # Position
        self.pos_x = self.create_spinbox_row("Position X", -1920, 1920)
        self.pos_y = self.create_spinbox_row("Position Y", -1080, 1080)
        
        # Scale
        self.scale_x = self.create_spinbox_row("Scale X", 0.1, 5.0, 0.1, 1.0)
        self.scale_y = self.create_spinbox_row("Scale Y", 0.1, 5.0, 0.1, 1.0)
        
        # Rotation
        self.rotation = self.create_spinbox_row("Rotation", -360, 360)
        
        # Opacity Section
        self.add_section_header("Opacity")
        self.opacity = self.create_slider_row("Opacity", 0, 100, 100)
        
        # Blend Mode
        self.add_section_header("Blend Mode")
        self.blend_mode = QComboBox()
        self.blend_mode.addItems(["Normal", "Screen", "Multiply", "Overlay", "Darken", "Lighten"])
        self.blend_mode.currentTextChanged.connect(self.on_value_changed)
        self.content_layout.addWidget(self.blend_mode)

        # Audio Section
        self.add_section_header("Audio")
        self.volume = self.create_slider_row("Volume", 0, 200, 100) # 100 = 1.0
        
        # Mute
        self.mute_chk = QCheckBox("Mute")
        self.mute_chk.stateChanged.connect(self.on_value_changed)
        self.content_layout.addWidget(self.mute_chk)
        
        # Fades
        self.fade_in = self.create_spinbox_row("Fade In (s)", 0.0, 10.0, 0.1, 0.0)
        self.fade_out = self.create_spinbox_row("Fade Out (s)", 0.0, 10.0, 0.1, 0.0)

        # Color Section
        self.add_section_header("Color Correction")
        self.brightness = self.create_slider_row("Brightness", -100, 100, 0) # -1.0 to 1.0
        self.contrast = self.create_slider_row("Contrast", 0, 200, 100) # 0.0 to 2.0
        self.saturation = self.create_slider_row("Saturation", 0, 200, 100) # 0.0 to 2.0
        self.hue = self.create_slider_row("Hue", -180, 180, 0)

        # Disable by default
        self.set_enabled(False)

    def add_section_header(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; color: #90CAF9; margin-top: 10px;")
        self.content_layout.addWidget(label)

    def create_spinbox_row(self, label_text, min_val, max_val, step=1.0, default=0.0):
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setSingleStep(step)
        spinbox.setValue(default)
        spinbox.valueChanged.connect(self.on_value_changed)
        
        layout.addWidget(label, 0, 0)
        layout.addWidget(spinbox, 0, 1)
        
        self.content_layout.addWidget(container)
        return spinbox

    def create_slider_row(self, label_text, min_val, max_val, default):
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        slider.valueChanged.connect(self.on_value_changed)
        
        layout.addWidget(label, 0, 0)
        layout.addWidget(slider, 0, 1)
        
        self.content_layout.addWidget(container)
        return slider

    def set_clip(self, clip: Clip):
        self.current_clip = clip
        if not clip:
            self.set_enabled(False)
            return
            
        self.set_enabled(True)
        # Block signals to prevent feedback loop
        self.block_signals(True)
        
        self.pos_x.setValue(clip.position_x)
        self.pos_y.setValue(clip.position_y)
        self.scale_x.setValue(clip.scale_x)
        self.scale_y.setValue(clip.scale_y)
        self.rotation.setValue(clip.rotation)
        self.opacity.setValue(int(clip.opacity * 100))
        self.blend_mode.setCurrentText(clip.blend_mode)
        
        self.volume.setValue(int(clip.volume * 100))
        self.mute_chk.setChecked(clip.muted)
        self.fade_in.setValue(clip.fade_in)
        self.fade_out.setValue(clip.fade_out)
        
        self.brightness.setValue(int(clip.brightness * 100))
        self.contrast.setValue(int(clip.contrast * 100))
        self.saturation.setValue(int(clip.saturation * 100))
        self.hue.setValue(int(clip.hue))
        
        self.block_signals(False)

    def set_enabled(self, enabled):
        self.content_widget.setEnabled(enabled)

    def block_signals(self, blocked):
        self.pos_x.blockSignals(blocked)
        self.pos_y.blockSignals(blocked)
        self.scale_x.blockSignals(blocked)
        self.scale_y.blockSignals(blocked)
        self.rotation.blockSignals(blocked)
        self.opacity.blockSignals(blocked)
        self.blend_mode.blockSignals(blocked)
        self.volume.blockSignals(blocked)
        self.mute_chk.blockSignals(blocked)
        self.fade_in.blockSignals(blocked)
        self.fade_out.blockSignals(blocked)
        self.brightness.blockSignals(blocked)
        self.contrast.blockSignals(blocked)
        self.saturation.blockSignals(blocked)
        self.hue.blockSignals(blocked)

    def on_value_changed(self):
        if not self.current_clip:
            return
            
        # Update clip model
        # TODO: Use Command Pattern for Undo/Redo here!
        self.current_clip.position_x = self.pos_x.value()
        self.current_clip.position_y = self.pos_y.value()
        self.current_clip.scale_x = self.scale_x.value()
        self.current_clip.scale_y = self.scale_y.value()
        self.current_clip.rotation = self.rotation.value()
        self.current_clip.opacity = self.opacity.value() / 100.0
        self.current_clip.blend_mode = self.blend_mode.currentText()
        
        self.current_clip.volume = self.volume.value() / 100.0
        self.current_clip.muted = self.mute_chk.isChecked()
        self.current_clip.fade_in = self.fade_in.value()
        self.current_clip.fade_out = self.fade_out.value()
        
        self.current_clip.brightness = self.brightness.value() / 100.0
        self.current_clip.contrast = self.contrast.value() / 100.0
        self.current_clip.saturation = self.saturation.value() / 100.0
        self.current_clip.hue = self.hue.value()
        
        # Emit signal or notify system to redraw player
        # For now, we assume direct object modification is enough for MVP, 
        # but Player needs to know to repaint.
        self.clip_changed.emit()
