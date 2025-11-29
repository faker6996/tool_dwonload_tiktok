from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QSpinBox,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut


class TextPanel(QFrame):
    """
    Simple Text panel for creating text clips on the timeline.
    """

    add_text_clip = pyqtSignal(str, float)  # text, duration (seconds)

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self.setup_ui()
        self.setup_shortcuts()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Text")
        title.setObjectName("panel_title")
        layout.addWidget(title)

        hint = QLabel("Enter text to add as a clip on the main track.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        layout.addWidget(hint)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Your text here...")
        layout.addWidget(self.text_edit)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        duration_label = QLabel("Duration (s):")
        duration_label.setStyleSheet("color: #a1a1aa;")
        controls.addWidget(duration_label)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 60)
        self.duration_spin.setValue(3)
        controls.addWidget(self.duration_spin)

        controls.addStretch()
        layout.addLayout(controls)

        add_btn = QPushButton("Add to Timeline")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.on_add_clicked)
        layout.addWidget(add_btn)

        layout.addStretch()

    def setup_shortcuts(self):
        """
        Bind Ctrl+Enter to add text to the timeline so user
        can quickly create text clips from the keyboard.
        """
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.on_add_clicked)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.on_add_clicked)

    def on_add_clicked(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            return

        duration = float(max(1, self.duration_spin.value()))
        self.add_text_clip.emit(text, duration)
