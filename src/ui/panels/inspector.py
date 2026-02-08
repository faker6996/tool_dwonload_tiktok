from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QWidget,
    QGridLayout,
    QSpinBox,
    QDoubleSpinBox,
    QSlider,
    QHBoxLayout,
    QScrollArea,
    QAbstractSpinBox,
    QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal
from contextlib import contextmanager
from src.ui.widgets.bounded_combobox import BoundedComboBox


class NoWheelSpinBox(QSpinBox):
    """SpinBox that ignores mouse wheel to avoid accidental value changes."""

    def wheelEvent(self, event):
        event.ignore()


class NoWheelDoubleSpinBox(QDoubleSpinBox):
    """DoubleSpinBox that ignores mouse wheel to avoid accidental value changes."""

    def wheelEvent(self, event):
        event.ignore()


class NoWheelSlider(QSlider):
    """Slider that ignores mouse wheel so scrolling only scrolls the panel."""

    def wheelEvent(self, event):
        event.ignore()


class ScaleValueProxy:
    """Compatibility adapter exposing normalized scale value as 1.0-based float."""

    def __init__(self, slider: QSlider):
        self._slider = slider

    def value(self) -> float:
        return self._slider.value() / 100.0

    def setValue(self, value: float) -> None:
        self._slider.setValue(int(value * 100))


class Inspector(QFrame):
    clip_changed = pyqtSignal(object)
    aspect_ratio_changed = pyqtSignal(str)

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
        self.content_widget = content_widget
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

        # Aspect Ratio Presets
        aspect_layout = QVBoxLayout()
        aspect_layout.setSpacing(8)
        aspect_label = QLabel("Aspect Ratio")
        aspect_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        self.aspect_combo = BoundedComboBox()
        self.aspect_combo.addItems(["Original", "16:9", "9:16", "4:3", "1:1"])
        self.aspect_combo.currentTextChanged.connect(self.on_aspect_ratio_changed)
        aspect_layout.addWidget(aspect_label)
        aspect_layout.addWidget(self.aspect_combo)
        self.content_layout.addLayout(aspect_layout)

        # Scale (only numeric + Reset, no visible slider)
        scale_container, self.scale_slider, self.scale_spin = self.create_slider_input("Scale", 1, 500, 100, "%")
        self.scale_x = ScaleValueProxy(self.scale_slider)
        self.content_layout.addWidget(scale_container)

        # Hide the slider and replace its row with a Reset button.
        scale_layout = scale_container.layout()
        if scale_layout is not None and self.scale_slider is not None:
            scale_layout.removeWidget(self.scale_slider)
            self.scale_slider.hide()

            self.scale_reset_btn = QPushButton("Reset")
            self.scale_reset_btn.setFixedWidth(60)
            self.scale_reset_btn.clicked.connect(self.reset_scale)
            scale_layout.addWidget(self.scale_reset_btn, 1, 0, 1, 2)

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
        self.blend_combo = BoundedComboBox()
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
        spin = NoWheelDoubleSpinBox()
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
        
        slider = NoWheelSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        
        spin = NoWheelSpinBox()
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

    def reset_scale(self):
        """
        Reset clip scale back to 100% and sync UI + player.
        """
        if not self.current_clip:
            return

        with block_signals(self.scale_spin, self.scale_slider):
            self.scale_spin.setValue(100)
            if self.scale_slider is not None:
                self.scale_slider.setValue(100)

        # update_clip_transform will read scale from the slider,
        # which we just synced above (even though it's hidden).
        self.update_clip_transform()

    def set_clip(self, clip):
        self.current_clip = clip
        enabled = clip is not None
        self.setEnabled(enabled)
        if hasattr(self, "content_widget"):
            self.content_widget.setEnabled(enabled)
        
        if not clip:
            return

        # Block signals to prevent feedback loop while UI reflects clip
        with block_signals(
            self.pos_x,
            self.pos_y,
            self.scale_slider,
            self.scale_spin,
            self.rotation_slider,
            self.rotation_spin,
            self.opacity_slider,
            self.opacity_spin,
            self.blend_combo,
            self.volume_slider,
            self.volume_spin,
        ):
            # Update UI from Clip Data
            self.pos_x.setValue(getattr(clip, 'position_x', 0))
            self.pos_y.setValue(getattr(clip, 'position_y', 0))
            self.scale_slider.setValue(int(getattr(clip, 'scale_x', 1.0) * 100))
            self.rotation_slider.setValue(int(getattr(clip, 'rotation', 0)))

            self.opacity_slider.setValue(int(getattr(clip, 'opacity', 1.0) * 100))
            self.blend_combo.setCurrentText(getattr(clip, 'blend_mode', 'Normal'))

            self.volume_slider.setValue(int(getattr(clip, 'volume', 1.0) * 100))

    def on_aspect_ratio_changed(self, text: str):
        self.aspect_ratio_changed.emit(text)

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


@contextmanager
def block_signals(*widgets):
    """
    Small helper to temporarily block signals on multiple widgets.
    Ensures signals are restored even if an exception occurs.
    """
    previous_states = []
    for w in widgets:
        if w is not None:
            previous_states.append((w, w.signalsBlocked()))
            w.blockSignals(True)
    try:
        yield
    finally:
        for w, prev in previous_states:
            w.blockSignals(prev)
