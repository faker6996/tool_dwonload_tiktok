import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QListWidget, QStackedWidget, QListWidgetItem, QLineEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

from .styles import DARK_THEME
from .pages.download_page import DownloadPage
from .pages.edit_page import EditPage
from .pages.document_page import DocumentPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Video Downloader")
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(QIcon("app_icon.png"))
        
        # Setup UI
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Layout (Horizontal: Sidebar + Right Content)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Sidebar (Left, Fixed Width) ---
        self.sidebar_container = QWidget()
        self.sidebar_container.setObjectName("sidebar_container")
        self.sidebar_container.setFixedWidth(200) # Reduced width
        self.sidebar_container.setStyleSheet("background-color: #161b22; border-right: 1px solid #30363d;") # Grayish background
        
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(10)

        # 1. App Logo/Title Area
        logo_widget = QWidget()
        logo_widget.setFixedHeight(60)
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(15, 15, 15, 10)
        
        icon_label = QLabel()
        icon_pixmap = QPixmap("app_icon.png")
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_layout.addWidget(icon_label)
        
        title_label = QLabel("Video Downloader") # Single line
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        logo_layout.addWidget(title_label)
        logo_layout.addStretch()
        
        sidebar_layout.addWidget(logo_widget)

        # 2. Navigation Menu
        self.sidebar = QListWidget()
        self.sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 15px;
                color: #8b949e;
                border-left: 3px solid transparent;
                margin-bottom: 2px;
                font-size: 13px;
            }
            QListWidget::item:selected {
                background-color: #21262d;
                color: #ffffff;
                border-left: 3px solid #58a6ff;
            }
            QListWidget::item:hover {
                background-color: #21262d;
                color: #c9d1d9;
            }
        """)
        
        self.add_sidebar_item("Download", "download")
        self.add_sidebar_item("Edit", "edit")
        self.add_sidebar_item("Document", "document")
        
        self.sidebar.currentRowChanged.connect(self.change_page)
        sidebar_layout.addWidget(self.sidebar)
        
        # 3. Bottom Section
        sidebar_layout.addStretch()
        
        user_widget = QWidget()
        user_widget.setFixedHeight(50)
        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(15, 10, 15, 10)
        user_label = QLabel("v1.0.0")
        user_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        user_layout.addWidget(user_label)
        sidebar_layout.addWidget(user_widget)

        main_layout.addWidget(self.sidebar_container)

        # --- Right Content Area ---
        right_container = QWidget()
        right_container.setStyleSheet("background-color: #0d1117;") 
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Header
        header_widget = QWidget()
        header_widget.setFixedHeight(60)
        header_widget.setStyleSheet("border-bottom: 1px solid #30363d; background-color: #0d1117;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search videos...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #161b22; 
                color: #c9d1d9; 
                padding: 6px 12px; 
                border-radius: 6px; 
                border: 1px solid #30363d;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #58a6ff;
            }
        """)
        header_layout.addWidget(self.search_input)
        header_layout.addStretch()
        
        # Right side icons
        # Removed for cleaner look as per user feedback about "2 bars"
        
        right_layout.addWidget(header_widget)

        # 2. Page Content
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #0d1117;")
        
        self.download_page = DownloadPage()
        self.edit_page = EditPage()
        self.document_page = DocumentPage()
        
        self.stacked_widget.addWidget(self.download_page)
        self.stacked_widget.addWidget(self.edit_page)
        self.stacked_widget.addWidget(self.document_page)
        
        right_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(right_container)
        
        # Set default page
        self.sidebar.setCurrentRow(0)

    def add_sidebar_item(self, name, icon_name):
        item = QListWidgetItem(name)
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # Placeholder for icons if we had them
        # item.setIcon(QIcon(f"assets/{icon_name}.png")) 
        self.sidebar.addItem(item)

    def change_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def apply_styles(self):
        self.setStyleSheet(DARK_THEME)

    def closeEvent(self, event):
        # Cleanup pages
        self.download_page.cleanup()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
