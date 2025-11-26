from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QGraphicsView, QGraphicsScene, 
                             QGraphicsRectItem, QGraphicsItem, QLabel, QWidget, QHBoxLayout, QCheckBox, QGraphicsObject)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPen, QTransform
from src.core.timeline.clip import Clip

class OverlayItem(QGraphicsObject):
    changed = pyqtSignal()

    def __init__(self, rect_size=200):
        super().__init__()
        self.rect_size = rect_size
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        self._pen = QPen(QColor("#90CAF9"), 4)
        self._brush = QBrush(Qt.BrushStyle.NoBrush)

    def boundingRect(self):
        return QRectF(-self.rect_size/2, -self.rect_size/2, self.rect_size, self.rect_size)

    def paint(self, painter, option, widget):
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawRect(self.boundingRect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Notify change (deferred to avoid recursion issues during drag)
            pass
        return super().itemChange(change, value)
    
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
            # Forward to parent Player if possible, or handle here
            # Since we need access to Player methods, let's emit a signal or call parent
            # But parent might be the layout container.
            # Easiest is to let Player handle it by passing the event or callback.
            # Or better: Player sets itself as parent and we call parent.
            if self.parent():
                # Try to find Player instance
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
        self.setObjectName("panel")
        self.setAcceptDrops(True) 
        self.current_clip = None
        self.scene = QGraphicsScene()
        
        self.setup_ui()

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
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title = QLabel("Player")
        title.setObjectName("panel_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Proxy Toggle
        self.proxy_chk = QCheckBox("Use Proxy")
        self.proxy_chk.stateChanged.connect(self.on_proxy_toggled)
        header_layout.addWidget(self.proxy_chk)
        
        layout.addWidget(header)
        
        # Graphics View
        self.view = DroppableGraphicsView(self.scene, self)
        self.view.setStyleSheet("border: none; background-color: #000;")
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        layout.addWidget(self.view)
        
        # Placeholder Screen
        self.canvas_width = 1920
        self.canvas_height = 1080
        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        
        # Background
        # Using addRect directly for background
        self.scene.addRect(0, 0, self.canvas_width, self.canvas_height, QPen(Qt.PenStyle.NoPen), QBrush(QColor("#000000")))
        
        # Overlay Item
        self.overlay_item = OverlayItem()
        self.overlay_item.hide()
        self.overlay_item.changed.connect(self.on_overlay_changed)
        self.scene.addItem(self.overlay_item)

    def set_clip(self, clip: Clip):
        self.current_clip = clip
        if not clip:
            self.overlay_item.hide()
            return
            
        self.overlay_item.show()
        self.update_overlay()

    def update_overlay(self):
        if not self.current_clip:
            return
            
        # Block signals to prevent feedback loop from Inspector updates
        self.overlay_item.blockSignals(True)
        
        # Calculate position relative to center
        center_x = self.canvas_width / 2
        center_y = self.canvas_height / 2
        
        self.overlay_item.setPos(center_x + self.current_clip.position_x, 
                                 center_y + self.current_clip.position_y)
        self.overlay_item.setRotation(self.current_clip.rotation)
        self.overlay_item.setScale(self.current_clip.scale_x) # Assuming uniform scale for now or handle X/Y separately
        
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

    def on_proxy_toggled(self, state):
        use_proxy = (state == Qt.CheckState.Checked.value)
        print(f"Proxy Mode: {'ON' if use_proxy else 'OFF'}")
        
        if self.current_clip and self.current_clip.proxy_path:
            # Logic to switch source would go here
            pass
