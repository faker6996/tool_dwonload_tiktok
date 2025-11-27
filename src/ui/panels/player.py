from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QGraphicsView, QGraphicsScene, 
                             QGraphicsRectItem, QGraphicsItem, QLabel, QWidget, QHBoxLayout, QCheckBox, QGraphicsObject, QPushButton, QSlider)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QUrl, QSizeF
from PyQt6.QtGui import QBrush, QColor, QPen, QTransform, QPainter
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from src.core.timeline.clip import Clip

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
        self.changed.emit()
    
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

class Player(QFrame):
    transform_changed = pyqtSignal() # Emitted when user interacts with overlay

    def __init__(self):
        super().__init__()
        self.setObjectName("player_panel")
        self.setAcceptDrops(True) 
        self.current_clip = None
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
            self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
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
        self.scene.addRect(0, 0, self.canvas_width, self.canvas_height, QPen(Qt.PenStyle.NoPen), QBrush(QColor("#000000")))
        
        # Video Text
        self.video_text = self.scene.addText("No Media")
        self.video_text.setDefaultTextColor(QColor("#505050"))
        self.video_text.setScale(5) # Larger text
        
        # Overlay Item (Transform Controls)
        self.overlay_item = OverlayItem(rect_size=self.canvas_width) # Match canvas size
        self.overlay_item.hide()
        self.overlay_item.changed.connect(self.on_overlay_changed)
        self.scene.addItem(self.overlay_item)

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
        if not clip:
            self.overlay_item.hide()
            self.video_item.hide()
            self.video_text.setPlainText("No Media")
            self.media_player.stop()
            self.media_player.setSource(QUrl())
            return
            
        # Show Video
        self.video_item.show()
        self.video_item.setSize(QSizeF(self.canvas_width, self.canvas_height))
        self.video_item.setPos(0, 0) # Video item is top-left based
        
        self.video_text.setPlainText(f"Preview: {clip.name}")
        
        # Center text
        br = self.video_text.boundingRect()
        scale = self.video_text.scale()
        self.video_text.setPos(self.canvas_width/2 - (br.width()*scale)/2, 
                               self.canvas_height/2 - (br.height()*scale)/2)
        
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
        self.overlay_item.blockSignals(True)
        
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
        
        # Update Video Item Transform matches Overlay
        # Since overlay and video are same size and centered, they share pos
        # BUT QGraphicsVideoItem is top-left based, Overlay is center based.
        # We need to adjust.
        # Actually, let's keep video item filling the screen and just transform it.
        # Wait, if we transform video item, we need to set its origin to center.
        
        self.video_item.setTransformOriginPoint(self.canvas_width / 2, self.canvas_height / 2)

        # Video item is top-left based, so convert center->top-left
        video_x = clip_center_x - (self.canvas_width / 2)
        video_y = clip_center_y - (self.canvas_height / 2)
        self.video_item.setPos(video_x, video_y)
        self.video_item.setRotation(self.current_clip.rotation)
        self.video_item.setScale(self.current_clip.scale_x)

        # Apply opacity (0.0 - 1.0)
        self.video_item.setOpacity(self.current_clip.opacity)

        # Apply volume (0.0 - 1.0)
        if hasattr(self, "audio_output"):
            self.audio_output.setVolume(self.current_clip.volume)
        
        self.overlay_item.blockSignals(False)

    def on_overlay_changed(self):
        if not self.current_clip:
            return
            
        # Sync Overlay -> Clip
        center_x = self.canvas_width / 2
        center_y = self.canvas_height / 2
        
        pos = self.overlay_item.pos()
        self.current_clip.position_x = pos.x() - center_x
        self.current_clip.position_y = pos.y() - center_y
        
        # Notify Inspector
        self.transform_changed.emit()
        
        # Update Video Item
        self.video_item.setTransformOriginPoint(self.canvas_width/2, self.canvas_height/2)
        self.video_item.setPos(self.current_clip.position_x, self.current_clip.position_y)

    def on_proxy_toggled(self, state):
        use_proxy = (state == Qt.CheckState.Checked.value)
        print(f"Proxy Mode: {'ON' if use_proxy else 'OFF'}")
        
        if self.current_clip and self.current_clip.proxy_path:
            # Logic to switch source would go here
            pass
