from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, 
                             QAbstractItemView, QPushButton, QFileDialog, QWidget, QHBoxLayout, QLineEdit, QComboBox, QToolButton)
from PyQt6.QtCore import Qt, QSize, QMimeData, QUrl, pyqtSignal
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QDrag, QPixmap, QColor, QBrush

import os
import re
from urllib.parse import urlparse

from src.core.state import state_manager
from src.core.api.stock_api import stock_api
from src.ui.threads import IngestionThread, StockDownloadThread


class AssetItemWidget(QWidget):
    """
    Custom widget to display a media item with a delete button.
    """
    delete_requested = pyqtSignal(str)

    def __init__(self, asset_id: str, name: str, icon: QIcon):
        super().__init__()
        self.asset_id = asset_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Thumbnail container (button overlays top-right of the image)
        self.thumb_container = QFrame()
        self.thumb_container.setStyleSheet("background-color: #27272a; border-radius: 5px;")
        self.thumb_container.setMinimumHeight(90)
        self.thumb_container.setFixedHeight(90)
        thumb_layout = QVBoxLayout(self.thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setSpacing(0)

        thumb_label = QLabel()
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = icon.pixmap(100, 80)
        thumb_label.setPixmap(pixmap)
        thumb_layout.addWidget(thumb_label)

        # Delete button - positioned at top-right corner using absolute positioning
        self.delete_btn = QToolButton(self.thumb_container)
        self.delete_btn.setText("×")  # Using × symbol for better appearance
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setFixedSize(22, 22)
        self.delete_btn.move(78, 3)  # Position at top-right (100-22=78, margin=3)
        self.delete_btn.setStyleSheet("""
            QToolButton {
                background-color: rgba(239, 68, 68, 0.95);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 11px;
                font-weight: bold;
                font-size: 16px;
                padding-bottom: 2px;
            }
            QToolButton:hover {
                background-color: rgba(248, 113, 113, 1);
                border: 1px solid rgba(255, 255, 255, 0.6);
            }
            QToolButton:pressed {
                background-color: rgba(220, 38, 38, 1);
            }
        """)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.asset_id))
        self.delete_btn.raise_()  # Ensure button is on top

        layout.addWidget(self.thumb_container)

        # Name label
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #e5e5e5; font-size: 11px;")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(30)
        layout.addWidget(name_label)

        self._position_delete_button()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_delete_button()

    def _position_delete_button(self):
        """Place delete button at top-right over the thumbnail."""
        if not hasattr(self, "thumb_container"):
            return
        margin = 3
        x = self.thumb_container.width() - self.delete_btn.width() - margin
        y = margin
        x = max(0, x)
        self.delete_btn.move(x, y)
        self.delete_btn.raise_()  # Keep button on top layer


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
        self.items_by_id = {}
        
        # Connect to State Manager (Keep original connection)
        state_manager.media_imported.connect(self.on_asset_imported)
        self.stock_download_thread = None

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

        # Stock Search (compatibility with existing tests/workflows)
        stock_search_row = QHBoxLayout()
        stock_search_row.setSpacing(8)
        self.stock_search_input = QLineEdit()
        self.stock_search_input.setPlaceholderText("Search stock media...")
        self.stock_search_input.returnPressed.connect(self.search_stock)
        self.stock_search_btn = QPushButton("Search Stock")
        self.stock_search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stock_search_btn.clicked.connect(self.search_stock)
        self.import_stock_btn = QPushButton("Import Selected")
        self.import_stock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_stock_btn.clicked.connect(self.import_selected_stock)
        stock_search_row.addWidget(self.stock_search_input)
        stock_search_row.addWidget(self.stock_search_btn)
        stock_search_row.addWidget(self.import_stock_btn)
        header_layout.addLayout(stock_search_row)
        
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

        self.stock_list = QListWidget()
        self.stock_list.setMaximumHeight(140)
        self.stock_list.itemDoubleClicked.connect(self.import_stock_item)
        self.stock_list.setStyleSheet("""
            QListWidget {
                background-color: #111111;
                border-top: 1px solid #27272a;
                border-left: none;
                border-right: none;
                border-bottom: none;
                color: #d4d4d8;
            }
            QListWidget::item {
                padding: 6px 8px;
            }
        """)
        layout.addWidget(self.stock_list)

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

        # Ignore drops that originate from within the media list itself to avoid duplicates
        if event.source() is self.asset_list:
            event.ignore()
            return

        files = [u.toLocalFile() for u in event.mimeData().urls()]
        files = [f for f in files if f] # Filter empty
        
        if files:
            self.import_media(files)
            
    def import_media(self, file_paths):
        # Skip files already in the media pool to prevent duplicates
        existing_paths = {a["target_url"] for a in state_manager.get_assets()}
        new_files = [p for p in file_paths if p not in existing_paths]
        if not new_files:
            return

        # Start Ingestion Thread
        self.thread = IngestionThread(new_files)
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

        # Attach custom widget with delete button
        widget = AssetItemWidget(asset["id"], asset["name"], item.icon())
        widget.delete_requested.connect(self.remove_asset)
        item.setSizeHint(widget.sizeHint())

        self.asset_list.addItem(item)
        self.asset_list.setItemWidget(item, widget)
        self.items_by_id[asset["id"]] = item

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

    def remove_asset(self, asset_id: str):
        """
        Remove asset from state and list view.
        """
        state_manager.remove_asset(asset_id)
        item = self.items_by_id.pop(asset_id, None)
        if item:
            row = self.asset_list.row(item)
            self.asset_list.takeItem(row)

    def search_stock(self):
        query = self.stock_search_input.text().strip()
        self.stock_list.clear()
        if not query:
            return

        results = stock_api.search_media(query, media_type="video")
        for item in results:
            title = item.get("title", "Untitled")
            list_item = QListWidgetItem(title)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.stock_list.addItem(list_item)

    def import_selected_stock(self):
        current_item = self.stock_list.currentItem()
        if current_item:
            self.import_stock_item(current_item)

    def import_stock_item(self, list_item: QListWidgetItem):
        stock_item = list_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(stock_item, dict):
            return
        self.download_stock_item(stock_item)

    def download_stock_item(self, stock_item: dict):
        if self.stock_download_thread and self.stock_download_thread.isRunning():
            return

        destination_path = self._build_stock_destination(stock_item)
        if os.path.exists(destination_path) and os.path.getsize(destination_path) > 0:
            self.import_media([destination_path])
            return

        self._set_stock_controls_enabled(False)
        self.stock_download_thread = StockDownloadThread(stock_item, destination_path)
        self.stock_download_thread.finished.connect(self.on_stock_download_finished)
        self.stock_download_thread.start()

    def on_stock_download_finished(self, success: bool, file_path: str, stock_item: dict):
        self._set_stock_controls_enabled(True)
        if success and file_path:
            self.import_media([file_path])

    def _set_stock_controls_enabled(self, enabled: bool):
        self.stock_search_input.setEnabled(enabled)
        self.stock_search_btn.setEnabled(enabled)
        self.stock_list.setEnabled(enabled)
        self.import_stock_btn.setEnabled(enabled)

    def _build_stock_destination(self, stock_item: dict) -> str:
        base_dir = os.path.join(os.path.expanduser("~"), ".video_downloader", "stock")
        os.makedirs(base_dir, exist_ok=True)

        media_id = self._sanitize_name(str(stock_item.get("id", "stock")))
        title = str(stock_item.get("title", media_id))
        safe_title = self._sanitize_name(title)
        extension = self._guess_media_extension(str(stock_item.get("url", "")))
        filename = f"{media_id}_{safe_title}{extension}"
        return os.path.join(base_dir, filename)

    def _sanitize_name(self, name: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_")
        return normalized[:80] or "stock_media"

    def _guess_media_extension(self, url: str) -> str:
        parsed = urlparse(url)
        extension = os.path.splitext(parsed.path)[1].lower()
        supported = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mp3", ".wav", ".m4a"}
        if extension in supported:
            return extension
        return ".mp4"
