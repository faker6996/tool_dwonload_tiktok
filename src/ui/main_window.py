import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QListWidget, QStackedWidget, QListWidgetItem)
from PyQt6.QtCore import Qt

from .styles import DARK_THEME
from .pages.download_page import DownloadPage
from .pages.edit_page import EditPage
from .pages.document_page import DocumentPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Video Downloader")
        self.setMinimumSize(1000, 700)
        
        # Setup UI
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Add items
        self.add_sidebar_item("Edit", "edit")
        self.add_sidebar_item("Download", "download")
        self.add_sidebar_item("Document", "document")
        
        self.sidebar.currentRowChanged.connect(self.change_page)
        main_layout.addWidget(self.sidebar)

        # Content Area
        self.stacked_widget = QStackedWidget()
        
        # Pages
        self.edit_page = EditPage()
        self.download_page = DownloadPage()
        self.document_page = DocumentPage()
        
        self.stacked_widget.addWidget(self.edit_page)
        self.stacked_widget.addWidget(self.download_page)
        self.stacked_widget.addWidget(self.document_page)
        
        main_layout.addWidget(self.stacked_widget)
        
        # Set default page (Download)
        self.sidebar.setCurrentRow(1)

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
