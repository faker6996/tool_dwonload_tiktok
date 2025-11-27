from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, 
                             QAbstractItemView, QPushButton, QFileDialog, QWidget, QHBoxLayout, QLineEdit, QComboBox)
from PyQt6.QtCore import Qt, QSize, QMimeData, QUrl
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QDrag, QPixmap, QColor, QBrush

import os

from src.core.state import state_manager
from src.ui.threads import IngestionThread

class DraggableListWidget(QListWidget):
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
            
        asset_id = item.data(Qt.ItemDataRole.UserRole)
        asset = state_manager.get_asset(asset_id)
        if not asset:
            return
            
        # Create MIME data
        mime_data = QMimeData()
        
        # 1. Set File URL (for compatibility with Player/Timeline expecting files)
        if "target_url" in asset:
            url = QUrl.fromLocalFile(asset["target_url"])
            mime_data.setUrls([url])
            
        # 2. Set Custom Data (Asset ID)
        mime_data.setText(asset_id)
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # Set Pixmap for drag visualization
        pixmap = item.icon().pixmap(100, 56)
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        
        drag.exec(supportedActions)

class MediaPool(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel") # Keep original object name for styling if needed
        self.setAcceptDrops(True) # Keep original drag/drop functionality
        self.setup_ui()
        
        # Connect to State Manager (Keep original connection)
        state_manager.media_imported.connect(self.on_asset_imported)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- Header (Import & Search) ---
        header_container = QWidget()
        header_container.setStyleSheet("background-color: #18181b; border-bottom: 1px solid #27272a;")
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(10)
        
        # Import Button
        self.import_btn = QPushButton("Import Media")
        self.import_btn.setObjectName("primary")
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.setFixedHeight(36)
        self.import_btn.clicked.connect(self.open_file_dialog) # Connect to existing open_file_dialog
        header_layout.addWidget(self.import_btn)
        
        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search assets...")
        self.search_input.textChanged.connect(self.filter_assets)
        header_layout.addWidget(self.search_input)
        
        layout.addWidget(header_container)
        
        # --- Asset Grid ---
        self.asset_list = DraggableListWidget() # Use DraggableListWidget
        self.asset_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.asset_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.asset_list.setGridSize(QSize(110, 130))
        self.asset_list.setSpacing(10)
        self.asset_list.setIconSize(QSize(100, 80))
        self.asset_list.setMovement(QListWidget.Movement.Static)
        self.asset_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection) # Keep original selection mode
        self.asset_list.setDragEnabled(True)
        self.asset_list.setStyleSheet("""
            QListWidget {
                background-color: #18181b;
                border: none;
                padding: 10px;
            }
            QListWidget::item {
                background-color: #27272a;
                border-radius: 5px;
                color: #a1a1aa;
                padding: 5px;
                text-align: center;
            }
            QListWidget::item:selected {
                background-color: #3f3f46;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #3f3f46;
            }
        """)
        
        layout.addWidget(self.asset_list)

    def open_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Media Files (*.mp4 *.mov *.avi *.mkv *.mp3 *.wav *.png *.jpg *.jpeg)") # Added .jpeg
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.import_media(file_paths)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("#panel { border: 2px solid #58a6ff; }")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("#panel { border: none; }")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("#panel { border: none; }")
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        files = [f for f in files if f] # Filter empty
        
        if files:
            self.import_media(files)
            
    def import_media(self, file_paths):
        # Start Ingestion Thread
        self.thread = IngestionThread(file_paths)
        self.thread.asset_processed.connect(self.handle_processed_asset)
        self.thread.start()
        
    def handle_processed_asset(self, asset):
        # Add to State Manager
        state_manager.add_asset(asset)
        
    def on_asset_imported(self, asset):
        # Update UI
        item = QListWidgetItem(asset["name"])
        item.setData(Qt.ItemDataRole.UserRole, asset["id"])
        item.setToolTip(asset["name"])
        
        # Set Icon
        thumb_path = asset["metadata"].get("thumbnailPath")
        if thumb_path:
            item.setIcon(QIcon(thumb_path))
        else:
            # Create a placeholder pixmap
            pixmap = QPixmap(100, 80) # Updated size to match iconSize
            pixmap.fill(QColor("#27272a")) # Use QColor for fill
            item.setIcon(QIcon(pixmap))
            
        self.asset_list.addItem(item)
        
        # Re-apply filter
        self.filter_assets()

    def filter_assets(self):
        search_text = self.search_input.text().lower()
        
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            asset_id = item.data(Qt.ItemDataRole.UserRole)
            asset = state_manager.get_asset(asset_id)
            
            if not asset:
                continue
                
            name_match = search_text in asset["name"].lower()
            item.setHidden(not name_match)
