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
from PyQt6.QtGui import QBrush, QColor, QPen, QTransform, QPainter, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from src.core.timeline.clip import Clip
from src.core.timeline.sticker import StickerClip
from contextlib import contextmanager
import json


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


class StickerItem(QGraphicsObject):
    """A sticker displayed on the player canvas with corner-drag resize and rotation."""
    changed = pyqtSignal()
    selected_signal = pyqtSignal(object)  # Emits self when selected

    def __init__(self, sticker_data: dict, parent=None):
        super().__init__(parent)
        self.sticker_data = sticker_data
        self.sticker_id = sticker_data.get("id", str(id(self)))
        self.content = sticker_data.get("content", "😀")
        self.sticker_type = sticker_data.get("type", "emoji")
        
        # Transform properties
        self._scale_factor = 1.0
        self._rotation = 0.0
        self._opacity = 1.0
        
        # Display size - larger default for better visibility
        self.base_size = 150
        
        # Resize state
        self._resizing = False
        self._resize_start_pos = None
        self._resize_start_scale = 1.0
        self._active_handle = None  # Which corner is being dragged
        self._handle_size = 12  # Larger handles for easier grabbing
        
        # Rotation state
        self._rotating = False
        self._rotate_start_pos = None
        self._rotate_start_angle = 0.0
        self._rotation_handle_distance = 30  # Distance of rotation handle from top edge
        
        # Flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Font for emoji - larger for better visibility
        self._font = QFont("Segoe UI Emoji", 72)
        
        # Selection border
        self._pen = QPen(QColor("#6366f1"), 3, Qt.PenStyle.DashLine)
        
        # Tooltip for user guidance
        self.setToolTip("🖱️ Drag center to move\n↔️ Drag corners to resize\n� Drag top circle to rotate\n�🗑️ Press Delete to remove")

    def boundingRect(self):
        size = self.base_size * self._scale_factor
        # Include handle areas and rotation handle in bounding rect
        margin = self._handle_size + self._rotation_handle_distance + 10
        return QRectF(-size/2 - margin, -size/2 - margin, size + margin*2, size + margin*2)

    def _get_handle_rects(self):
        """Return the 4 corner handle rectangles."""
        size = self.base_size * self._scale_factor
        r = size / 2
        hs = self._handle_size
        return {
            "tl": QRectF(-r - hs/2, -r - hs/2, hs, hs),
            "tr": QRectF(r - hs/2, -r - hs/2, hs, hs),
            "bl": QRectF(-r - hs/2, r - hs/2, hs, hs),
            "br": QRectF(r - hs/2, r - hs/2, hs, hs),
        }

    def _get_rotation_handle_rect(self):
        """Return the rotation handle circle rect (above the sticker)."""
        size = self.base_size * self._scale_factor
        r = size / 2
        hs = self._handle_size
        # Position above the top edge
        return QRectF(-hs/2, -r - self._rotation_handle_distance - hs/2, hs, hs)

    def _handle_at_pos(self, pos):
        """Check if pos is over a handle, return handle name or None."""
        if not self.isSelected():
            return None
        
        # Check rotation handle first
        rot_rect = self._get_rotation_handle_rect()
        if rot_rect.contains(pos):
            return "rotate"
        
        # Check corner handles
        handles = self._get_handle_rects()
        for name, rect in handles.items():
            if rect.contains(pos):
                return name
        return None

    def paint(self, painter, option, widget):
        painter.setOpacity(self._opacity)
        
        # Apply rotation transform
        painter.save()
        painter.rotate(self._rotation)
        
        # Draw emoji/text - scale font with sticker size
        scaled_font = QFont(self._font)
        scaled_font.setPointSizeF(self._font.pointSizeF() * self._scale_factor)
        painter.setFont(scaled_font)
        painter.setPen(QColor("#ffffff"))
        
        size = self.base_size * self._scale_factor
        emoji_rect = QRectF(-size/2, -size/2, size, size)
        painter.drawText(emoji_rect, Qt.AlignmentFlag.AlignCenter, self.content)
        
        painter.restore()
        
        # Draw selection border and handles if selected (not rotated, in item coords)
        if self.isSelected():
            painter.save()
            painter.rotate(self._rotation)
            
            painter.setPen(self._pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(emoji_rect)
            
            # Draw corner handles - larger and more visible
            handles = self._get_handle_rects()
            for name, rect in handles.items():
                # Highlight active handle
                if name == self._active_handle:
                    painter.setBrush(QBrush(QColor("#6366f1")))
                else:
                    painter.setBrush(QBrush(QColor("#ffffff")))
                painter.setPen(QPen(QColor("#6366f1"), 2))
                painter.drawRect(rect)
            
            # Draw rotation handle (circle above sticker)
            rot_rect = self._get_rotation_handle_rect()
            
            # Draw line connecting rotation handle to sticker
            painter.setPen(QPen(QColor("#6366f1"), 2))
            painter.drawLine(0, int(-size/2), 0, int(-size/2 - self._rotation_handle_distance))
            
            # Draw rotation circle
            if self._active_handle == "rotate":
                painter.setBrush(QBrush(QColor("#6366f1")))
            else:
                painter.setBrush(QBrush(QColor("#22c55e")))  # Green for rotation
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawEllipse(rot_rect)
            
            painter.restore()

    def hoverMoveEvent(self, event):
        """Change cursor when hovering over handles."""
        # Need to account for rotation when checking handle positions
        handle = self._handle_at_pos(self._rotate_point(event.pos(), -self._rotation))
        if handle == "rotate":
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif handle:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor if handle in ["tl", "br"] else Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().hoverMoveEvent(event)

    def _rotate_point(self, point, angle):
        """Rotate a point around origin by angle degrees."""
        import math
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        x = point.x() * cos_a - point.y() * sin_a
        y = point.x() * sin_a + point.y() * cos_a
        from PyQt6.QtCore import QPointF
        return QPointF(x, y)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Transform mouse position to account for current rotation
            rotated_pos = self._rotate_point(event.pos(), -self._rotation)
            handle = self._handle_at_pos(rotated_pos)
            
            if handle == "rotate":
                # Start rotating
                self._rotating = True
                self._active_handle = "rotate"
                self._rotate_start_pos = event.pos()
                self._rotate_start_angle = self._rotation
                event.accept()
                self.update()
                return
            elif handle:
                # Start resizing
                self._resizing = True
                self._active_handle = handle
                self._resize_start_pos = rotated_pos
                self._resize_start_scale = self._scale_factor
                event.accept()
                self.update()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        import math
        
        if self._rotating and self._rotate_start_pos is not None:
            # Calculate rotation angle based on mouse position relative to center
            pos = event.pos()
            angle = math.degrees(math.atan2(pos.x(), -pos.y()))
            
            self._rotation = angle
            self.prepareGeometryChange()
            self.update()
            event.accept()
            return
            
        if self._resizing and self._resize_start_pos:
            # Transform mouse position to account for rotation
            rotated_pos = self._rotate_point(event.pos(), -self._rotation)
            delta = rotated_pos - self._resize_start_pos
            
            # Use diagonal distance for uniform scaling
            drag_distance = (delta.x() + delta.y()) / 2
            
            # Invert for top-left handle
            if self._active_handle in ["tl"]:
                drag_distance = -drag_distance
            elif self._active_handle == "tr":
                drag_distance = (delta.x() - delta.y()) / 2
            elif self._active_handle == "bl":
                drag_distance = (-delta.x() + delta.y()) / 2
            
            # Scale factor change based on drag
            scale_change = drag_distance / 100  # Sensitivity
            new_scale = self._resize_start_scale + scale_change
            new_scale = max(0.3, min(5.0, new_scale))
            
            if new_scale != self._scale_factor:
                self.prepareGeometryChange()
                self._scale_factor = new_scale
                self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._rotating:
            self._rotating = False
            self._active_handle = None
            self._rotate_start_pos = None
            self.changed.emit()
            self.update()
            event.accept()
            return
        if self._resizing:
            self._resizing = False
            self._active_handle = None
            self._resize_start_pos = None
            self.changed.emit()
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)
        self.changed.emit()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value:
                self.selected_signal.emit(self)
        return super().itemChange(change, value)

    def keyPressEvent(self, event):
        # Delete sticker with Delete or Backspace key
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            # Find player and remove this sticker
            scene = self.scene()
            if scene:
                for view in scene.views():
                    player = view.parent()
                    while player:
                        if hasattr(player, 'remove_sticker'):
                            player.remove_sticker(self)
                            return
                        player = player.parent()
        super().keyPressEvent(event)

    def set_scale(self, scale: float):
        self._scale_factor = max(0.1, min(5.0, scale))
        self.prepareGeometryChange()
        self.update()

    def get_transform_data(self) -> dict:
        """Return current transform data for saving."""
        pos = self.pos()
        return {
            "position_x": pos.x(),
            "position_y": pos.y(),
            "scale": self._scale_factor,
            "rotation": self._rotation,
            "opacity": self._opacity,
        }

class DroppableGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        # Accept both file URLs and sticker data
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-sticker"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-sticker"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Handle sticker drop
        if event.mimeData().hasFormat("application/x-sticker"):
            parent = self.parent()
            while parent:
                if hasattr(parent, "handle_sticker_drop"):
                    parent.handle_sticker_drop(event)
                    return
                parent = parent.parent()
            event.accept()
        elif event.mimeData().hasUrls():
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
    sticker_added = pyqtSignal(dict)  # Emitted when sticker is added to canvas
    media_dropped = pyqtSignal(str)  # Emitted when media file is dropped (path)

    def __init__(self):
        super().__init__()
        self.setObjectName("player_panel")
        self.setAcceptDrops(True) 
        self.current_clip = None
        # Offset (in seconds) of the current clip on the main timeline
        self.timeline_offset = 0.0
        self.scene = QGraphicsScene()
        self.aspect_ratio_preset = "Original"
        
        # Stickers on canvas
        self.stickers = []  # List of StickerItem
        
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
                # Also emit signal so timeline can add clip
                self.media_dropped.emit(file_path)

    def handle_sticker_drop(self, event):
        """Handle sticker drop from Effects panel."""
        if event.mimeData().hasFormat("application/x-sticker"):
            data = event.mimeData().data("application/x-sticker")
            sticker_data = json.loads(bytes(data).decode('utf-8'))
            
            # Get drop position in scene coordinates
            view_pos = event.position().toPoint()
            scene_pos = self.view.mapToScene(view_pos)
            
            self.add_sticker(sticker_data, scene_pos.x(), scene_pos.y())
            event.accept()

    def add_sticker(self, sticker_data: dict, x: float = None, y: float = None):
        """Add a sticker to the canvas."""
        sticker_item = StickerItem(sticker_data)
        
        # Position at center if not specified
        if x is None:
            x = self.canvas_width / 2
        if y is None:
            y = self.canvas_height / 2
        
        sticker_item.setPos(x, y)
        sticker_item.changed.connect(self.on_sticker_changed)
        sticker_item.selected_signal.connect(self.on_sticker_selected)
        
        self.scene.addItem(sticker_item)
        self.stickers.append(sticker_item)
        
        # Emit signal for timeline integration
        self.sticker_added.emit({
            **sticker_data,
            "position_x": x - self.canvas_width / 2,
            "position_y": y - self.canvas_height / 2,
        })
        
        return sticker_item

    def remove_sticker(self, sticker_item):
        """Remove a sticker from the canvas."""
        if sticker_item in self.stickers:
            self.scene.removeItem(sticker_item)
            self.stickers.remove(sticker_item)

    def on_sticker_changed(self):
        """Handle sticker transform changes."""
        self.transform_changed.emit()

    def on_sticker_selected(self, sticker_item):
        """Handle sticker selection."""
        # Deselect video overlay when sticker is selected
        if hasattr(self, 'overlay_item'):
            self.overlay_item.setSelected(False)

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
