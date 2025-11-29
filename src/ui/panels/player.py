from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsItem,
    QLabel,
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QGraphicsObject,
    QPushButton,
    QSlider,
    QGraphicsColorizeEffect,
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QUrl, QSizeF
from PyQt6.QtGui import QBrush, QColor, QPen, QTransform, QPainter
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from src.core.timeline.clip import Clip
from contextlib import contextmanager


@contextmanager
def block_signals(*objects):
    """
    Temporarily block Qt signals for the provided objects.
    Ensures signals are always restored, even if an exception occurs.
    """
    previous_states = []
    for obj in objects:
        if obj is not None:
            previous_states.append((obj, obj.signalsBlocked()))
            obj.blockSignals(True)
    try:
        yield
    finally:
        for obj, prev in previous_states:
            obj.blockSignals(prev)

class OverlayItem(QGraphicsObject):
    changed = pyqtSignal()

    def __init__(self, rect_size=200):
        super().__init__()
        self.rect_size = rect_size
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        self._pen = QPen(QColor("#4f46e5"), 2, Qt.PenStyle.DashLine)
        self._brush = QBrush(Qt.BrushStyle.NoBrush)

    def boundingRect(self):
        return QRectF(-self.rect_size/2, -self.rect_size/2, self.rect_size, self.rect_size)

    def paint(self, painter, option, widget):
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawRect(self.boundingRect())
        
        # Draw handles
        handle_size = 8.0
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        r = self.rect_size / 2
        
        # Use QRectF for float coordinates
        painter.drawRect(QRectF(-r - handle_size/2, -r - handle_size/2, handle_size, handle_size)) # TL
        painter.drawRect(QRectF(r - handle_size/2, -r - handle_size/2, handle_size, handle_size))  # TR
        painter.drawRect(QRectF(-r - handle_size/2, r - handle_size/2, handle_size, handle_size))  # BL
        painter.drawRect(QRectF(r - handle_size/2, r - handle_size/2, handle_size, handle_size))   # BR

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            pass
        return super().itemChange(change, value)

    def set_rect_size(self, rect_size: float):
        if rect_size == self.rect_size:
            return
        self.prepareGeometryChange()
        self.rect_size = rect_size
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.changed.emit()

class DroppableGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            if self.parent():
                parent = self.parent()
                while parent:
                    if hasattr(parent, "handle_drop"):
                        parent.handle_drop(event)
                        return
                    parent = parent.parent()
            event.accept()
        else:
            event.ignore()

    def wheelEvent(self, event):
        """
        Forward mouse wheel events up to a parent that can handle scaling.
        This lets the Player decide how to interpret the wheel (e.g. scale clip).
        """
        parent = self.parent()
        while parent:
            if hasattr(parent, "handle_wheel"):
                parent.handle_wheel(event)
                return
            parent = parent.parent()
        super().wheelEvent(event)

class Player(QFrame):
    transform_changed = pyqtSignal()  # Emitted when user interacts with overlay
    playhead_changed = pyqtSignal(float)  # Timeline time in seconds

    def __init__(self):
        super().__init__()
        self.setObjectName("player_panel")
        self.setAcceptDrops(True) 
        self.current_clip = None
        # Offset (in seconds) of the current clip on the main timeline
        self.timeline_offset = 0.0
        self.scene = QGraphicsScene()
        self.aspect_ratio_preset = "Original"
        
        # Styling
        self.setStyleSheet("""
            #player_panel {
                background-color: #09090b;
                border-right: 1px solid #27272a;
            }
            QLabel {
                color: #a1a1aa;
                font-family: 'Inter';
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #a1a1aa;
            }
            QPushButton:hover {
                background-color: #27272a;
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                border: 1px solid #27272a;
                height: 4px;
                background: #18181b;
                margin: 0px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #a1a1aa;
                border: 1px solid #a1a1aa;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #ffffff;
                border-color: #ffffff;
            }
        """)
        
        self.setup_ui()
        self.setup_media_player()

    def setup_media_player(self):
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # Video Item
        self.video_item = QGraphicsVideoItem()
        self.video_item.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.scene.addItem(self.video_item)
        self.media_player.setVideoOutput(self.video_item)

        # Color effect placeholder for future color correction presets
        self.color_effect = QGraphicsColorizeEffect()
        self.color_effect.setStrength(0.0)
        self.video_item.setGraphicsEffect(self.color_effect)
        
        # Connect signals
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.video_item.nativeSizeChanged.connect(self.on_video_native_size_changed)

    def on_video_native_size_changed(self, size):
        if not size.isValid():
            return

        # If aspect ratio is "Original", match canvas to native video size.
        if self.aspect_ratio_preset == "Original":
            self.canvas_width = size.width()
            self.canvas_height = size.height()

        # Update scene rect and background to match the canvas.
        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        if hasattr(self, "background_rect"):
            self.background_rect.setRect(0, 0, self.canvas_width, self.canvas_height)

        # In all cases, make sure video fills the current canvas.
        self.video_item.setSize(QSizeF(self.canvas_width, self.canvas_height))

        # Update overlay size to roughly match the canvas bounds.
        if hasattr(self, "overlay_item"):
            self.overlay_item.set_rect_size(min(self.canvas_width, self.canvas_height))

        # Recompute positions using the new canvas size so the
        # clip stays centered the first time we load it.
        if self.current_clip:
            self.update_overlay()

        if self.zoom_slider.value() == 100:
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def handle_drop(self, event):
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls()]
            if files:
                file_path = files[0]
                self.load_clip_from_path(file_path)

    def load_clip_from_path(self, file_path):
        # Create a temporary clip for preview
        from src.core.timeline.clip import Clip
        from src.core.state import state_manager
        
        asset = None
        if hasattr(state_manager, "state") and "media_pool" in state_manager.state:
             for a in state_manager.state["media_pool"]["assets"].values():
                if a["target_url"] == file_path:
                    asset = a
                    break
        
        duration = 5.0
        if asset:
            duration = asset["metadata"].get("duration", 5.0)
            
        clip = Clip(
            asset_id=file_path,
            name=file_path.split("/")[-1],
            duration=duration
        )
        self.set_clip(clip)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.handle_drop(event)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- Top Bar ---
        header = QWidget()
        header.setFixedHeight(40)
        header.setStyleSheet("background-color: #18181b; border-bottom: 1px solid #27272a;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(12)
        
        title = QLabel("Player")
        title.setStyleSheet("font-weight: 600; color: #e4e4e7;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Proxy Toggle
        self.proxy_chk = QCheckBox("Use Proxy")
        self.proxy_chk.setStyleSheet("""
            QCheckBox { color: #a1a1aa; spacing: 8px; }
            QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #52525b; background: #27272a; }
            QCheckBox::indicator:checked { background: #6366f1; border-color: #6366f1; }
        """)
        self.proxy_chk.stateChanged.connect(self.on_proxy_toggled)
        header_layout.addWidget(self.proxy_chk)
        
        layout.addWidget(header)
        
        # --- Main View Area ---
        view_container = QWidget()
        view_container.setStyleSheet("background-color: #09090b;")
        view_layout = QVBoxLayout(view_container)
        view_layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = DroppableGraphicsView(self.scene, self)
        self.view.setStyleSheet("border: none; background: transparent;")
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        
        view_layout.addWidget(self.view)
        layout.addWidget(view_container)
        
        # --- Bottom Control Bar ---
        controls = QWidget()
        controls.setFixedHeight(48)
        controls.setStyleSheet("background-color: #18181b; border-top: 1px solid #27272a;")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(16, 0, 16, 0)
        controls_layout.setSpacing(16)
        
        # Playback Controls
        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_play.clicked.connect(self.toggle_playback)
        self.btn_next = QPushButton("⏭")
        
        for btn in [self.btn_prev, self.btn_play, self.btn_next]:
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_next)
        
        # Timecode
        self.timecode_label = QLabel("00:00:00:00")
        self.timecode_label.setStyleSheet("font-family: 'JetBrains Mono', monospace; color: #6366f1; font-weight: 600;")
        controls_layout.addWidget(self.timecode_label)
        
        # Scrubber (Progress)
        self.scrubber = QSlider(Qt.Orientation.Horizontal)
        self.scrubber.setRange(0, 1000)
        self.scrubber.setValue(0)
        self.scrubber.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.scrubber)
        
        # Duration
        self.duration_label = QLabel("00:00:00:00")
        self.duration_label.setStyleSheet("font-family: 'JetBrains Mono', monospace; color: #71717a;")
        controls_layout.addWidget(self.duration_label)
        
        # Zoom Controls
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(4)
        
        btn_zoom_out = QPushButton("-")
        btn_zoom_out.setFixedSize(24, 24)
        btn_zoom_out.clicked.connect(lambda: self.zoom_slider.setValue(self.zoom_slider.value() - 10))
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setFixedWidth(80)
        self.zoom_slider.setRange(10, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.set_zoom)
        
        btn_zoom_in = QPushButton("+")
        btn_zoom_in.setFixedSize(24, 24)
        btn_zoom_in.clicked.connect(lambda: self.zoom_slider.setValue(self.zoom_slider.value() + 10))
        
        zoom_layout.addWidget(btn_zoom_out)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(btn_zoom_in)
        
        controls_layout.addLayout(zoom_layout)
        
        layout.addWidget(controls)
        
        self.init_scene()

    def init_scene(self):
        # Placeholder Screen
        self.canvas_width = 1920
        self.canvas_height = 1080
        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        
        # Background
        self.background_rect = self.scene.addRect(
            0,
            0,
            self.canvas_width,
            self.canvas_height,
            QPen(Qt.PenStyle.NoPen),
            QBrush(QColor("#000000")),
        )
        
        # Video Text
        self.video_text = self.scene.addText("No Media")
        self.video_text.setDefaultTextColor(QColor("#505050"))
        self.video_text.setScale(5) # Larger text
        self.center_text_in_canvas()
        
        # Overlay Item (Transform Controls)
        self.overlay_item = OverlayItem(rect_size=self.canvas_width) # Match canvas size
        self.overlay_item.hide()
        self.overlay_item.changed.connect(self.on_overlay_changed)
        self.scene.addItem(self.overlay_item)

    def center_text_in_canvas(self):
        """
        Center the overlay text within the current canvas dimensions.
        Safe to call whenever canvas size or text changes.
        """
        if not hasattr(self, "video_text") or self.video_text is None:
            return

        br = self.video_text.boundingRect()
        scale = self.video_text.scale()
        x = self.canvas_width / 2 - (br.width() * scale) / 2
        y = self.canvas_height / 2 - (br.height() * scale) / 2
        self.video_text.setPos(x, y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Only auto-fit if zoom is at 100% (default) so manual zoom is respected
        if self.view and self.scene and self.zoom_slider.value() == 100:
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_aspect_ratio(self, preset: str):
        """
        Update the player canvas based on an aspect ratio preset.
        Presets: "Original", "16:9", "9:16", "4:3", "1:1"
        """
        self.aspect_ratio_preset = preset

        if preset == "Original":
            native = self.video_item.nativeSize()
            if native.isValid():
                self.canvas_width = native.width()
                self.canvas_height = native.height()
        else:
            aspect_map = {
                "16:9": (1920, 1080),
                "9:16": (1080, 1920),
                "4:3": (1440, 1080),
                "1:1": (1080, 1080),
            }
            if preset not in aspect_map:
                return
            self.canvas_width, self.canvas_height = aspect_map[preset]

        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        if hasattr(self, "background_rect"):
            self.background_rect.setRect(0, 0, self.canvas_width, self.canvas_height)
        self.video_item.setSize(QSizeF(self.canvas_width, self.canvas_height))

        if hasattr(self, "overlay_item"):
            self.overlay_item.set_rect_size(min(self.canvas_width, self.canvas_height))

        if self.current_clip:
            self.update_overlay()

        if self.zoom_slider.value() == 100:
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_zoom(self, value):
        # Value is percentage (10-200)
        scale = value / 100.0
        transform = QTransform()
        transform.scale(scale, scale)
        self.view.setTransform(transform)

    def set_clip(self, clip: Clip):
        self.current_clip = clip
        # Remember clip position on main timeline (seconds)
        self.timeline_offset = getattr(clip, "start_time", 0.0) if clip else 0.0
        if not clip:
            self.overlay_item.hide()
            self.video_item.hide()
            self.video_text.setPlainText("No Media")
            self.center_text_in_canvas()
            self.media_player.stop()
            self.media_player.setSource(QUrl())
            return

        is_text_clip = getattr(clip, "clip_type", "video") == "text"

        if is_text_clip:
            # Hide video playback and show text content instead
            self.media_player.stop()
            self.media_player.setSource(QUrl())
            self.video_item.hide()

            text = clip.text_content or clip.name
            self.video_text.setPlainText(text)

            # Apply basic font styling from clip
            font = self.video_text.font()
            font.setPointSize(getattr(clip, "font_size", 24))
            self.video_text.setFont(font)

            color = QColor(getattr(clip, "font_color", "#FFFFFF"))
            self.video_text.setDefaultTextColor(color)

            self.center_text_in_canvas()
            self.overlay_item.show()
            self.update_overlay()
            return

        # Video clip: show video output and preview name
        self.video_item.show()
        self.video_item.setSize(QSizeF(self.canvas_width, self.canvas_height))

        self.video_text.setPlainText(f"Preview: {clip.name}")
        self.center_text_in_canvas()
        
        self.overlay_item.show()
        self.update_overlay()
        
        # When a new clip is loaded, reset the zoom (if user
        # has not changed it) so the video fits nicely in view.
        if self.zoom_slider.value() == 100:
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # Play Media
        self.media_player.setSource(QUrl.fromLocalFile(clip.asset_id))
        self.media_player.play()
        self.btn_play.setText("⏸")

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.btn_play.setText("▶")
        else:
            self.media_player.play()
            self.btn_play.setText("⏸")

    def on_position_changed(self, position):
        self.scrubber.setValue(position)
        self.timecode_label.setText(self.format_time(position))
        # position (ms) -> seconds on global timeline
        timeline_time = (position / 1000.0) + float(self.timeline_offset or 0.0)
        self.playhead_changed.emit(timeline_time)

    def on_duration_changed(self, duration):
        self.scrubber.setRange(0, duration)
        self.duration_label.setText(self.format_time(duration))

    def set_position(self, position):
        self.media_player.setPosition(position)

    def format_time(self, ms):
        seconds = (ms // 1000) % 60
        minutes = (ms // 60000) % 60
        hours = (ms // 3600000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:00"

    def update_overlay(self, clip: Clip | None = None):
        if clip is not None:
            self.current_clip = clip

        if not self.current_clip:
            return

        # Block signals to prevent feedback loop from Inspector updates
        with block_signals(self.overlay_item):
            # Canvas center
            center_x = self.canvas_width / 2
            center_y = self.canvas_height / 2

            # Clip center in scene coordinates
            clip_center_x = center_x + self.current_clip.position_x
            clip_center_y = center_y + self.current_clip.position_y

            # Overlay (center-based)
            self.overlay_item.setPos(clip_center_x, clip_center_y)
            self.overlay_item.setRotation(self.current_clip.rotation)
            self.overlay_item.setScale(self.current_clip.scale_x) 

            is_text_clip = getattr(self.current_clip, "clip_type", "video") == "text"

            if is_text_clip:
                # Position text item so its center matches the clip center
                self.video_text.setScale(self.current_clip.scale_x)
                br = self.video_text.boundingRect()
                scaled_width = br.width() * self.video_text.scale()
                scaled_height = br.height() * self.video_text.scale()

                text_x = clip_center_x - scaled_width / 2
                text_y = clip_center_y - scaled_height / 2
                self.video_text.setPos(text_x, text_y)
                self.video_text.setRotation(self.current_clip.rotation)
            else:
                # Update Video Item Transform matches Overlay
                # Since overlay and video are same size and centered, they share pos
                # BUT QGraphicsVideoItem is top-left based, Overlay is center based.
                # We need to adjust.
                self.video_item.setTransformOriginPoint(self.canvas_width / 2, self.canvas_height / 2)

                # Video item is top-left based, so convert center->top-left
                video_x = clip_center_x - (self.canvas_width / 2)
                video_y = clip_center_y - (self.canvas_height / 2)
                self.video_item.setPos(video_x, video_y)
                self.video_item.setRotation(self.current_clip.rotation)
                self.video_item.setScale(self.current_clip.scale_x)

                # Apply opacity, blend mode, and color correction
                self.apply_blend_mode()
                self.apply_color_correction()

        # Apply volume (0.0 - 1.0)
        if hasattr(self, "audio_output"):
            self.audio_output.setVolume(self.current_clip.volume)

    def on_overlay_changed(self):
        if not self.current_clip:
            return
            
        # Sync Overlay -> Clip
        center_x = self.canvas_width / 2
        center_y = self.canvas_height / 2
        
        pos = self.overlay_item.pos()
        self.current_clip.position_x = pos.x() - center_x
        self.current_clip.position_y = pos.y() - center_y

        # Notify Inspector and re-apply unified transform logic
        self.transform_changed.emit()
        self.update_overlay()

    def apply_blend_mode(self):
        """
        Apply the clip's blend mode to the video item.
        For now we approximate blend modes by adjusting opacity, since the
        current player renders a single layer over a solid background.
        This can be extended later when multi-layer compositing is added.
        """
        if not self.current_clip:
            return

        base_opacity = self.current_clip.opacity
        mode = getattr(self.current_clip, "blend_mode", "Normal")

        # Simple approximation: tweak opacity per mode
        if mode == "Normal":
            opacity = base_opacity
        elif mode == "Multiply":
            # Darker feel
            opacity = base_opacity * 0.8
        elif mode == "Screen":
            # Slightly brighter / lighter
            opacity = min(1.0, base_opacity + 0.15)
        elif mode == "Overlay":
            opacity = min(1.0, base_opacity + 0.05)
        elif mode == "Darken":
            opacity = base_opacity * 0.7
        elif mode == "Lighten":
            opacity = min(1.0, base_opacity + 0.25)
        else:
            opacity = base_opacity

        self.video_item.setOpacity(opacity)

    def apply_color_correction(self):
        """
        Apply simple color tint based on the clip's color correction properties.
        This is an approximation using QGraphicsColorizeEffect so that presets
        like Sepia / Cool / Warm have some visual feedback in the player.
        """
        if not self.current_clip:
            return

        if getattr(self.current_clip, "clip_type", "video") != "video":
            # Only apply to video clips for now
            if hasattr(self, "color_effect"):
                self.color_effect.setStrength(0.0)
            return

        if not hasattr(self, "color_effect"):
            return

        # Derive a tint color from hue and saturation
        hue = float(getattr(self.current_clip, "hue", 0.0))
        saturation = float(getattr(self.current_clip, "saturation", 1.0))
        brightness = float(getattr(self.current_clip, "brightness", 0.0))

        # Normalize hue to 0-359 for QColor.fromHsl
        h = int((hue + 360.0) % 360.0)

        # Strength depends on how far saturation/brightness deviate from neutral
        sat_delta = abs(saturation - 1.0)
        bri_delta = abs(brightness)
        strength = min(1.0, sat_delta * 0.7 + bri_delta * 0.5)

        if strength <= 0.01:
            # No visible correction, disable effect
            self.color_effect.setStrength(0.0)
            return

        # Build a soft tint color; l=127 gives mid-lightness
        tint = QColor.fromHsl(h, 180, 127)
        self.color_effect.setColor(tint)
        self.color_effect.setStrength(strength)

    def on_proxy_toggled(self, state):
        use_proxy = (state == Qt.CheckState.Checked.value)
        print(f"Proxy Mode: {'ON' if use_proxy else 'OFF'}")
        
        if self.current_clip and self.current_clip.proxy_path:
            # Logic to switch source would go here
            pass

    def handle_wheel(self, event):
        """
        Handle mouse wheel over the player view to scale the current clip.
        Scroll up = zoom in, scroll down = zoom out.
        """
        if not self.current_clip:
            return

        delta = event.angleDelta().y()
        if delta == 0:
            return

        # Each notch (120) changes scale by 5%
        step = 0.05
        direction = 1 if delta > 0 else -1
        new_scale = self.current_clip.scale_x + direction * step

        # Clamp to a reasonable range
        new_scale = max(0.1, min(new_scale, 5.0))

        # Update clip scale (uniform)
        self.current_clip.scale_x = new_scale
        self.current_clip.scale_y = new_scale

        # Apply to scene and notify inspector
        self.update_overlay()
        self.transform_changed.emit()
        event.accept()
