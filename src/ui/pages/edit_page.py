from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class EditPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Edit Video")
        title.setObjectName("page_title")
        layout.addWidget(title)
        
        content = QLabel("Video editing features coming soon...")
        content.setStyleSheet("color: #888888; font-size: 16px;")
        content.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(content)
        layout.addStretch()
