from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QPushButton, QTabWidget, QWidget)
from PyQt6.QtCore import Qt
from src.core.settings.shortcuts import shortcut_manager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        # Shortcuts Tab
        shortcuts_tab = QWidget()
        shortcuts_layout = QVBoxLayout(shortcuts_tab)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.populate_shortcuts()
        
        shortcuts_layout.addWidget(self.table)
        tabs.addTab(shortcuts_tab, "Shortcuts")
        
        # General Tab (Placeholder)
        general_tab = QWidget()
        tabs.addTab(general_tab, "General")
        
        layout.addWidget(tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

    def populate_shortcuts(self):
        self.table.setRowCount(len(shortcut_manager.shortcuts))
        
        for i, (action_id, shortcut) in enumerate(shortcut_manager.shortcuts.items()):
            name_item = QTableWidgetItem(shortcut.name)
            name_item.setFlags(name_item.flags() ^ Qt.ItemFlag.ItemIsEditable) # Read only
            
            key_item = QTableWidgetItem(shortcut.key_sequence)
            # Make key editable (simplified for MVP, ideally capture key press)
            
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, key_item)
