# Color Palette - Design System
"""
App sử dụng Dark Theme với màu chủ đạo Blue-Purple gradient

PRIMARY COLORS:
- Primary Blue: #58a6ff (Bright Blue - Main accent)
- Primary Purple: #8b5cf6 (Vivid Purple - Secondary accent)
- Primary Gradient: Blue → Purple

BACKGROUND COLORS:
- Background Base: #121212 (Deepest black)
- Background Panel: #1E1E1E (Panel background)
- Background Input: #252526 (Input fields)
- Background Hover: #2C2C2C (Hover states)

BORDER & DIVIDER:
- Border Primary: #2C2C2C
- Border Accent: #3E3E3E
- Border Highlight: #90CAF9

TEXT COLORS:
- Text Primary: #E0E0E0 (Main text)
- Text Secondary: #8b9dc3 (Muted text)
- Text Highlight: #FFFFFF (Bright text)

ACCENT COLORS (cho các tính năng):
- Success: #10B981 (Green)
- Warning: #F59E0B (Orange)
- Error: #EF4444 (Red)
- Info: #3B82F6 (Blue)
"""

DARK_THEME = """
/* Global Reset */
QWidget {
    background-color: #121212;
    color: #E0E0E0;
    font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
    font-size: 13px;
}

/* Main Window */
QMainWindow {
    background-color: #121212;
}

/* --- SIDEBAR STYLES (Restored) --- */
QWidget#sidebar_container {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(26, 31, 58, 0.95), 
                                stop:1 rgba(15, 18, 35, 0.95));
    border-right: 1px solid rgba(88, 166, 255, 0.2);
}

/* Specific styling for the Sidebar ListWidget */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    padding: 10px 16px;
    color: #8b9dc3;
    border-left: 3px solid transparent;
    margin: 2px 8px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
}

QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(88, 166, 255, 0.2), 
                                stop:1 rgba(139, 92, 246, 0.2));
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #c9d1d9;
}

/* --- PANEL STYLES (New Module 0) --- */

/* Splitter Handle */
QSplitter::handle {
    background-color: #1E1E1E;
    border: 1px solid #2C2C2C;
}

QSplitter::handle:hover {
    background-color: #90CAF9;
}

/* Panels (Media Pool, Inspector, etc.) */
QFrame#panel {
    background-color: #1E1E1E;
    border: 1px solid #2C2C2C;
    border-radius: 4px;
}

QLabel#panel_title {
    font-weight: bold;
    color: #A0A0A0;
    padding: 5px;
    background-color: #252526;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

/* Buttons - Using Primary Blue-Purple Gradient */
QPushButton {
    background-color: #2C2C2C;
    color: #E0E0E0;
    border: 1px solid #3E3E3E;
    padding: 6px 12px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #3E3E3E;
    border-color: #505050;
}

QPushButton:pressed {
    background-color: #1E1E1E;
}

QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #58a6ff, stop:1 #8b5cf6);
    color: white;
    border: none;
}

QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #4a8fd9, stop:1 #7645d9);
}

/* Input Fields */
QLineEdit {
    background-color: #252526;
    color: #E0E0E0;
    border: 1px solid #3E3E3E;
    padding: 5px;
    border-radius: 4px;
}

QLineEdit:focus {
    border: 1px solid #90CAF9;
    background-color: #1E1E1E;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #121212;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #424242;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #121212;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #424242;
    min-width: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ComboBox */
QComboBox {
    background-color: #252526;
    color: #E0E0E0;
    border: 1px solid #3E3E3E;
    padding: 5px 10px;
    border-radius: 4px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #505050;
    background-color: #2C2C2C;
}

QComboBox:focus {
    border-color: #90CAF9;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #E0E0E0;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #252526;
    border: 1px solid #3E3E3E;
    selection-background-color: #90CAF9;
    selection-color: #FFFFFF;
    padding: 4px;
}

/* Slider - Using Primary Gradient */
QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #3E3E3E;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #58a6ff, stop:1 #8b5cf6);
    border: none;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #6bb4ff, stop:1 #9d6fff);
}

/* TabWidget */
QTabWidget::pane {
    border: 1px solid #2C2C2C;
    background-color: #1E1E1E;
    border-radius: 4px;
}

QTabBar::tab {
    background: #252526;
    color: #8b9dc3;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #2C2C2C;
    border-bottom: none;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #2C2C2C, stop:1 #1E1E1E);
    color: #FFFFFF;
    border-top: 2px solid #90CAF9;
}

QTabBar::tab:hover:!selected {
    background-color: #2C2C2C;
    color: #c9d1d9;
}

/* CheckBox - Using Primary Gradient */
QCheckBox {
    spacing: 8px;
    color: #E0E0E0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #3E3E3E;
    border-radius: 3px;
    background-color: #252526;
}

QCheckBox::indicator:hover {
    border-color: #505050;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #58a6ff, stop:1 #8b5cf6);
    border-color: #58a6ff;
}

QCheckBox::indicator:checked:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #6bb4ff, stop:1 #9d6fff);
}

/* ProgressBar - Using Primary Gradient */
QProgressBar {
    border: 1px solid #3E3E3E;
    border-radius: 4px;
    text-align: center;
    background-color: #252526;
    color: #FFFFFF;
    height: 20px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #58a6ff, stop:1 #8b5cf6);
    border-radius: 3px;
}

/* Dialog Styling */
QDialog {
    background-color: #1E1E1E;
}

QDialog QLabel {
    color: #E0E0E0;
}

/* SpinBox */
QSpinBox, QDoubleSpinBox {
    background-color: #252526;
    color: #E0E0E0;
    border: 1px solid #3E3E3E;
    padding: 4px;
    border-radius: 4px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #90CAF9;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: #2C2C2C;
    border-left: 1px solid #3E3E3E;
    border-top-right-radius: 3px;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #2C2C2C;
    border-left: 1px solid #3E3E3E;
    border-bottom-right-radius: 3px;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-bottom: 4px solid #E0E0E0;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-top: 4px solid #E0E0E0;
}
"""
