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
        self.sidebar_container.setFixedWidth(220) # Slightly wider for modern look
        # Styles handled by DARK_THEME stylesheet
        
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
        # Styles handled by DARK_THEME stylesheet
        
        self.add_sidebar_item("📥 Download", "download")
        self.add_sidebar_item("✂️ Edit", "edit")
        self.add_sidebar_item("📚 Document", "document")
        self.add_sidebar_item("⚙️ Settings", "settings")
        
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
        # Styles handled by DARK_THEME stylesheet
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Header
        header_widget = QWidget()
        header_widget.setFixedHeight(70)
        header_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 rgba(22, 27, 34, 0.8), 
                                        stop:1 rgba(10, 14, 39, 0.6));
            border-bottom: 1px solid rgba(88, 166, 255, 0.15);
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        # Page Title Label (shows current menu)
        self.page_title_label = QLabel("📥 Download")
        self.page_title_label.setStyleSheet("""
            color: #ffffff; 
            font-size: 20px;
            font-weight: 600;
        """)
        header_layout.addWidget(self.page_title_label)
        header_layout.addStretch()
        
        # Version label
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: rgba(139, 157, 195, 0.5); font-size: 12px;")
        header_layout.addWidget(version_label)
        
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
        # Handle Settings (Index 3)
        if index == 3:
            self.open_settings()
            # Revert selection to previous page or keep it? 
            # Better to not change page.
            # Let's just keep the previous selection visually? 
            # Or just open dialog.
            # For now, let's switch back to previous if possible, or just ignore page switch.
            # But QStackedWidget needs an index. 
            # Let's assume Settings is not a page in StackedWidget.
            
            # Restore previous selection (hacky but works for now)
            # self.sidebar.setCurrentIndex(...) 
            return

        self.stacked_widget.setCurrentIndex(index)
        # Update header title based on selected menu
        menu_titles = ["📥 Download", "✂️ Edit", "📚 Document"]
        if 0 <= index < len(menu_titles):
            self.page_title_label.setText(menu_titles[index])

    def open_settings(self):
        from src.ui.dialogs.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()

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
