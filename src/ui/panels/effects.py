from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QTabWidget
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon

class Effects(QFrame):
    effect_selected = pyqtSignal(str)  # Name of filter/effect

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        title = QLabel("Effects")
        title.setObjectName("panel_title")
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: #2C2C2C; color: #BBB; padding: 8px 12px; }
            QTabBar::tab:selected { background: #3A3A3A; color: #FFF; border-bottom: 2px solid #90CAF9; }
        """)
        
        # Filters Tab
        self.filters_list = QListWidget()
        self.filters_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.filters_list.setIconSize(QSize(60, 60))
        self.filters_list.setSpacing(10)
        self.filters_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.filters_list.itemClicked.connect(self.on_filter_clicked)

        self.populate_filters()
        tabs.addTab(self.filters_list, "Filters")
        
        # Stickers Tab
        self.stickers_list = QListWidget()
        self.stickers_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.stickers_list.setIconSize(QSize(60, 60))
        self.stickers_list.setSpacing(10)
        
        self.populate_stickers()
        tabs.addTab(self.stickers_list, "Stickers")
        
        layout.addWidget(tabs)

    def populate_filters(self):
        filters = ["Sepia", "B&W", "Vivid", "Cool", "Warm", "Vintage"]
        for f in filters:
            item = QListWidgetItem(f)
            # item.setIcon(QIcon(f"assets/filters/{f.lower()}.png")) # Placeholder
            self.filters_list.addItem(item)

    def populate_stickers(self):
        stickers = ["Emoji", "Arrow", "Star", "Heart"]
        for s in stickers:
            item = QListWidgetItem(s)
            self.stickers_list.addItem(item)

    def on_filter_clicked(self, item: QListWidgetItem):
        if not item:
            return
        name = item.text()
        self.effect_selected.emit(name)
