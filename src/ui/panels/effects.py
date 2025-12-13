from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, 
    QTabWidget, QHBoxLayout, QPushButton, QWidget, QScrollArea,
    QGridLayout
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QMimeData, QByteArray
from PyQt6.QtGui import QIcon, QDrag, QFont
import json

# Sticker data organized by category
STICKER_DATA = {
    "emojis": [
        {"name": "Smile", "content": "😀", "type": "emoji"},
        {"name": "Laugh", "content": "😂", "type": "emoji"},
        {"name": "Heart Eyes", "content": "😍", "type": "emoji"},
        {"name": "Cool", "content": "😎", "type": "emoji"},
        {"name": "Fire", "content": "🔥", "type": "emoji"},
        {"name": "Star", "content": "⭐", "type": "emoji"},
        {"name": "Heart", "content": "❤️", "type": "emoji"},
        {"name": "Thumbs Up", "content": "👍", "type": "emoji"},
        {"name": "Clap", "content": "👏", "type": "emoji"},
        {"name": "Party", "content": "🎉", "type": "emoji"},
        {"name": "Rocket", "content": "🚀", "type": "emoji"},
        {"name": "Check", "content": "✅", "type": "emoji"},
    ],
    "shapes": [
        {"name": "Circle", "content": "⬤", "type": "shape"},
        {"name": "Square", "content": "■", "type": "shape"},
        {"name": "Triangle", "content": "▲", "type": "shape"},
        {"name": "Diamond", "content": "◆", "type": "shape"},
        {"name": "Star Shape", "content": "★", "type": "shape"},
        {"name": "Heart Shape", "content": "♥", "type": "shape"},
    ],
    "arrows": [
        {"name": "Arrow Up", "content": "⬆️", "type": "arrow"},
        {"name": "Arrow Down", "content": "⬇️", "type": "arrow"},
        {"name": "Arrow Left", "content": "⬅️", "type": "arrow"},
        {"name": "Arrow Right", "content": "➡️", "type": "arrow"},
        {"name": "Curved Arrow", "content": "↩️", "type": "arrow"},
        {"name": "Double Arrow", "content": "↔️", "type": "arrow"},
    ],
    "decorations": [
        {"name": "Sparkles", "content": "✨", "type": "decoration"},
        {"name": "Rainbow", "content": "🌈", "type": "decoration"},
        {"name": "Crown", "content": "👑", "type": "decoration"},
        {"name": "Medal", "content": "🏅", "type": "decoration"},
        {"name": "Gift", "content": "🎁", "type": "decoration"},
        {"name": "Balloon", "content": "🎈", "type": "decoration"},
    ],
}


class StickerButton(QPushButton):
    """A clickable sticker button with emoji display."""
    
    def __init__(self, sticker_data: dict, parent=None):
        super().__init__(parent)
        self.sticker_data = sticker_data
        self.setFixedSize(50, 50)
        self.setText(sticker_data["content"])
        self.setFont(QFont("Segoe UI Emoji", 24))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(sticker_data["name"])
        self.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: 1px solid #3E3E3E;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3E3E3E;
                border-color: #6366f1;
            }
            QPushButton:pressed {
                background-color: #4f46e5;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Start drag operation
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # Encode sticker data as JSON
            data = json.dumps(self.sticker_data).encode('utf-8')
            mime_data.setData("application/x-sticker", QByteArray(data))
            mime_data.setText(self.sticker_data["content"])
            
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.CopyAction)
        
        super().mousePressEvent(event)


class Effects(QFrame):
    effect_selected = pyqtSignal(str)  # Name of filter/effect
    sticker_selected = pyqtSignal(dict)  # Sticker data when clicked
    sticker_added = pyqtSignal(dict)  # When sticker should be added to canvas

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self.current_category = "emojis"
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        title = QLabel("Effects")
        title.setObjectName("panel_title")
        layout.addWidget(title)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: #2C2C2C; color: #BBB; padding: 8px 12px; }
            QTabBar::tab:selected { background: #3A3A3A; color: #FFF; border-bottom: 2px solid #6366f1; }
        """)
        
        # Filters Tab
        self.filters_list = QListWidget()
        self.filters_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.filters_list.setIconSize(QSize(60, 60))
        self.filters_list.setSpacing(10)
        self.filters_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.filters_list.itemClicked.connect(self.on_filter_clicked)
        self.filters_list.setStyleSheet("""
            QListWidget { background-color: #1E1E1E; border: none; }
            QListWidget::item { background-color: #2C2C2C; border-radius: 6px; padding: 8px; }
            QListWidget::item:hover { background-color: #3E3E3E; }
            QListWidget::item:selected { background-color: #4f46e5; }
        """)
        self.populate_filters()
        self.tabs.addTab(self.filters_list, "Filters")
        
        # Stickers Tab
        stickers_widget = QWidget()
        stickers_layout = QVBoxLayout(stickers_widget)
        stickers_layout.setContentsMargins(8, 8, 8, 8)
        stickers_layout.setSpacing(8)
        
        # Category Buttons
        category_widget = QWidget()
        category_layout = QHBoxLayout(category_widget)
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.setSpacing(4)
        
        self.category_buttons = {}
        categories = [
            ("emojis", "😀"),
            ("shapes", "■"),
            ("arrows", "➡️"),
            ("decorations", "✨"),
        ]
        
        for cat_id, cat_icon in categories:
            btn = QPushButton(cat_icon)
            btn.setFixedSize(36, 36)
            btn.setFont(QFont("Segoe UI Emoji", 16))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(cat_id == "emojis")
            btn.clicked.connect(lambda checked, c=cat_id: self.on_category_changed(c))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2C2C2C;
                    border: 1px solid #3E3E3E;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #3E3E3E;
                }
                QPushButton:checked {
                    background-color: #4f46e5;
                    border-color: #6366f1;
                }
            """)
            category_layout.addWidget(btn)
            self.category_buttons[cat_id] = btn
        
        category_layout.addStretch()
        stickers_layout.addWidget(category_widget)
        
        # Stickers Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #1E1E1E; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.stickers_container = QWidget()
        self.stickers_grid = QGridLayout(self.stickers_container)
        self.stickers_grid.setSpacing(8)
        self.stickers_grid.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.stickers_container)
        stickers_layout.addWidget(scroll)
        
        self.populate_stickers()
        self.tabs.addTab(stickers_widget, "Stickers")
        
        layout.addWidget(self.tabs)

    def populate_filters(self):
        filters = ["Sepia", "B&W", "Vivid", "Cool", "Warm", "Vintage"]
        for f in filters:
            item = QListWidgetItem(f)
            self.filters_list.addItem(item)

    def populate_stickers(self):
        # Clear existing stickers
        while self.stickers_grid.count():
            item = self.stickers_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add stickers for current category
        stickers = STICKER_DATA.get(self.current_category, [])
        cols = 4
        for i, sticker in enumerate(stickers):
            btn = StickerButton(sticker)
            btn.clicked.connect(lambda checked, s=sticker: self.on_sticker_clicked(s))
            row = i // cols
            col = i % cols
            self.stickers_grid.addWidget(btn, row, col)
        
        # Add spacer at bottom
        spacer_row = (len(stickers) // cols) + 1
        self.stickers_grid.setRowStretch(spacer_row, 1)

    def on_category_changed(self, category: str):
        self.current_category = category
        # Update button states
        for cat_id, btn in self.category_buttons.items():
            btn.setChecked(cat_id == category)
        self.populate_stickers()

    def on_filter_clicked(self, item: QListWidgetItem):
        if not item:
            return
        name = item.text()
        self.effect_selected.emit(name)

    def on_sticker_clicked(self, sticker_data: dict):
        """Handle sticker click - emit signal to add to canvas."""
        self.sticker_selected.emit(sticker_data)
        self.sticker_added.emit(sticker_data)
