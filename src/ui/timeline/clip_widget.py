from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QRect
from PyQt6.QtGui import QDrag, QPainter, QPixmap, QColor

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
        self.update_style()
        
        # Load waveform if exists
        if self.clip.waveform_path:
            self.waveform_pixmap = QPixmap(self.clip.waveform_path)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        name_label = QLabel(clip.name)
        name_label.setStyleSheet("color: #E0E0E0; font-size: 11px; background: transparent; border: none;")
        layout.addWidget(name_label)
        
    def update_style(self):
        border_color = "#90CAF9" if self.is_selected else "#505050"
        bg_color = "#4A4A4A" if self.is_selected else "#3A3A3A"
        
        # We use paintEvent for background to support waveform, so we simplify stylesheet
        self.setStyleSheet(f"""
            #clip_widget {{
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            #clip_widget:hover {{
                border-color: #90CAF9;
            }}
        """)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()
        self.update() # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Background
        bg_color = QColor("#4A4A4A") if self.is_selected else QColor("#3A3A3A")
        painter.fillRect(self.rect(), bg_color)
        
        # Draw Waveform
        if self.waveform_pixmap:
            # Draw waveform with some transparency or blending
            target_rect = self.rect().adjusted(2, 2, -2, -2)
            painter.setOpacity(0.6)
            painter.drawPixmap(target_rect, self.waveform_pixmap)
            painter.setOpacity(1.0)
            
        # Draw Text Content (for Subtitles)
        if self.clip.clip_type == "text":
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(self.rect().adjusted(5, 0, -5, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.clip.text_content)
            
        # Draw Border (handled by stylesheet usually, but we can reinforce if needed)
        # super().paintEvent(event) # Stylesheet handling

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
            mime.setText(self.clip.id) # Pass clip ID
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)
