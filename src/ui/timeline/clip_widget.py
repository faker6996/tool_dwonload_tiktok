from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QRect
from PyQt6.QtGui import QDrag, QPainter, QPixmap, QColor, QPen, QBrush

class ClipWidget(QFrame):
    """
    Visual representation of a Clip on the timeline.
    """
    clicked = pyqtSignal(object) # Emits self (ClipWidget)

    def __init__(self, clip, parent=None):
        super().__init__(parent)
        self.clip = clip
        self.is_selected = False
        self.waveform_pixmap = None
        
        self.setObjectName("clip_widget")
        # No stylesheet here, we use paintEvent for full control
        
        # Load waveform if exists
        if self.clip.waveform_path:
            self.waveform_pixmap = QPixmap(self.clip.waveform_path)
            
        # We don't use layout for labels anymore, we draw them
        
    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update() # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Determine Colors based on Type
        is_audio = getattr(self.clip, 'is_audio', False) or self.clip.asset_id.endswith(('.mp3', '.wav'))
        # Note: Clip model might not have is_audio, check asset extension or metadata if possible.
        # For now, let's assume if it has waveform it's audio, or check extension.
        
        if is_audio:
            bg_color = QColor("#1e3a2f") # Dark Green
            border_color = QColor("#10B981") # Bright Green
            accent_color = QColor("#059669")
        else:
            bg_color = QColor("#2b3a4f") # Dark Blue
            border_color = QColor("#58a6ff") # Bright Blue
            accent_color = QColor("#1f6feb")
            
        if self.is_selected:
            bg_color = bg_color.lighter(130)
            border_color = QColor("#FFFFFF")
            
        # Draw Background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, 4, 4)
        
        # Draw "Film Strip" holes for Video
        if not is_audio:
            painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
            # Top holes
            for x in range(0, rect.width(), 15):
                painter.drawRect(x + 2, 2, 8, 4)
            # Bottom holes
            for x in range(0, rect.width(), 15):
                painter.drawRect(x + 2, rect.height() - 6, 8, 4)
        
        # Draw Waveform for Audio
        if is_audio and self.waveform_pixmap:
            target_rect = rect.adjusted(2, 10, -2, -10)
            painter.setOpacity(0.8)
            painter.drawPixmap(target_rect, self.waveform_pixmap)
            painter.setOpacity(1.0)
            
        # Draw Border
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(border_color)
        pen.setWidth(2 if self.is_selected else 1)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Draw Text
        painter.setPen(QColor("#FFFFFF"))
        text_rect = rect.adjusted(10, 0, -10, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.clip.name)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(str(self.clip.asset_id)) # Pass ID
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)
