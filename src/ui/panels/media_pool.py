from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, 
                             QAbstractItemView, QPushButton, QFileDialog, QWidget, QHBoxLayout, QLineEdit, QComboBox, QTabWidget)
from PyQt6.QtCore import Qt, QSize, QMimeData, QUrl
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QDrag

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

class MediaPool(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self.setAcceptDrops(True)
        
        self.setup_ui()
        
        # Connect to State Manager
        state_manager.media_imported.connect(self.on_asset_imported)

    def open_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Media Files (*.mp4 *.mov *.avi *.mkv *.mp3 *.wav *.png *.jpg)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.import_media(file_paths)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- Tab 1: Local Media ---
        local_tab = QWidget()
        local_layout = QVBoxLayout(local_tab)
        local_layout.setContentsMargins(0, 5, 0, 0)
        
        # Title & Import
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 0, 5, 0)
        title = QLabel("Local Media")
        title.setObjectName("panel_title")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.import_btn = QPushButton("📁 Import Media")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 7px 16px;
                border-radius: 5px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #7890ff, stop:1 #8b5fc3);
            }
        """)
        self.import_btn.clicked.connect(self.open_file_dialog)
        header_layout.addWidget(self.import_btn)
        local_layout.addLayout(header_layout)
        
        # Search & Filter
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(5, 0, 5, 5)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search local...")
        self.search_input.textChanged.connect(self.filter_assets)
        filter_layout.addWidget(self.search_input)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Video", "Audio", "Image"])
        self.filter_combo.currentTextChanged.connect(self.filter_assets)
        filter_layout.addWidget(self.filter_combo)
        local_layout.addLayout(filter_layout)
        
        # Asset List
        self.asset_list = DraggableListWidget()
        self.asset_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.asset_list.setIconSize(QSize(100, 56))
        self.asset_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.asset_list.setGridSize(QSize(120, 90))
        self.asset_list.setSpacing(10)
        self.asset_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.asset_list.setDragEnabled(True)
        local_layout.addWidget(self.asset_list)
        
        self.tabs.addTab(local_tab, "Local")
        
        # --- Tab 2: Stock Media ---
        stock_tab = QWidget()
        stock_layout = QVBoxLayout(stock_tab)
        stock_layout.setContentsMargins(0, 5, 0, 0)
        
        # Stock Search
        stock_search_layout = QHBoxLayout()
        stock_search_layout.setContentsMargins(5, 0, 5, 5)
        self.stock_search_input = QLineEdit()
        self.stock_search_input.setPlaceholderText("Search Pexels/Unsplash...")
        self.stock_search_input.returnPressed.connect(self.search_stock)
        stock_search_layout.addWidget(self.stock_search_input)
        stock_btn = QPushButton("Search")
        stock_btn.clicked.connect(self.search_stock)
        stock_search_layout.addWidget(stock_btn)
        stock_layout.addLayout(stock_search_layout)
        
        # Stock Results List
        self.stock_list = QListWidget()
        self.stock_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.stock_list.setIconSize(QSize(100, 56))
        self.stock_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.stock_list.setGridSize(QSize(120, 90))
        self.stock_list.setSpacing(10)
        stock_layout.addWidget(self.stock_list)
        
        self.tabs.addTab(stock_tab, "Stock")
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("#panel { border: 2px solid #90CAF9; }")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("#panel { border: 1px solid #2C2C2C; }")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("#panel { border: 1px solid #2C2C2C; }")
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
        # Add to State Manager (which will emit signal back to us, but we can also add directly)
        # Better to go through State Manager to ensure single source of truth
        state_manager.add_asset(asset)
        
    def on_asset_imported(self, asset):
        # Update UI
        item = QListWidgetItem(asset["name"])
        item.setData(Qt.ItemDataRole.UserRole, asset["id"])
        
        # Set Icon
        thumb_path = asset["metadata"].get("thumbnailPath")
        if thumb_path:
            item.setIcon(QIcon(thumb_path))
        else:
            item.setIcon(QIcon("assets/default_video.png")) # Fallback
            
        self.asset_list.addItem(item)
        
        # Re-apply filter
        self.filter_assets()

    def filter_assets(self):
        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()
        
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            asset_id = item.data(Qt.ItemDataRole.UserRole)
            asset = state_manager.get_asset(asset_id)
            
            if not asset:
                continue
                
            name_match = search_text in asset["name"].lower()
            
            type_match = True
            if filter_type != "All":
                # Determine type from metadata or extension?
                # We don't have explicit type field in asset dict yet, infer from metadata or file extension
                # Or check metadata keys.
                # Let's check metadata "codec" or similar, or just extension.
                # Ideally StateManager should provide type.
                # For now, let's use a simple helper or check metadata.
                
                # Check if audio or video stream exists in metadata?
                # Our ingestion returns "width"/"height" for video.
                is_video = asset["metadata"].get("width", 0) > 0
                is_audio = asset["metadata"].get("width", 0) == 0 and asset["metadata"].get("duration", 0) > 0
                # Image? duration 0?
                
                if filter_type == "Video" and not is_video:
                    type_match = False
                elif filter_type == "Audio" and not is_audio:
                    type_match = False
                elif filter_type == "Image":
                    # TODO: Add image detection logic
                    type_match = False 
            
            item.setHidden(not (name_match and type_match))

    def search_stock(self):
        query = self.stock_search_input.text()
        if not query:
            return
            
        from src.core.api.stock_api import stock_api
        results = stock_api.search_media(query)
        
        self.stock_list.clear()
        for res in results:
            item = QListWidgetItem(res["title"])
            # In real app, load thumbnail from URL asynchronously
            item.setIcon(QIcon("assets/default_video.png")) 
            item.setToolTip(f"Duration: {res['duration']}s")
            self.stock_list.addItem(item)
