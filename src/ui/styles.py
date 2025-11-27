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

/* --- SIDEBAR STYLES --- */
QWidget#sidebar_container {
    background-color: #121212;
    border-right: 1px solid #2C2C2C;
}

/* Specific styling for the Sidebar ListWidget */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    padding: 12px 16px;
    color: #8b9dc3;
    border-left: 3px solid transparent;
    margin: 4px 8px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
}

QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 rgba(88, 166, 255, 0.15), 
                                stop:1 rgba(139, 92, 246, 0.15));
    color: #58a6ff;
    border-left: 3px solid #58a6ff;
}

QListWidget::item:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #c9d1d9;
}

/* --- PANEL STYLES --- */

/* Splitter Handle */
QSplitter::handle {
    background-color: #121212;
    border: 1px solid #121212;
}

QSplitter::handle:hover {
    background-color: #58a6ff;
}

/* Panels (Media Pool, Inspector, etc.) */
QFrame#panel {
    background-color: #1E1E1E;
    border: none;
    border-radius: 0px;
}

QLabel#panel_title {
    font-weight: 600;
    color: #FFFFFF;
    padding: 10px 15px;
    background-color: transparent;
    font-size: 14px;
}

/* Buttons */
QPushButton {
    background-color: #2C2C2C;
    color: #E0E0E0;
    border: 1px solid #3E3E3E;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 500;
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
                                stop:0 #6bb4ff, stop:1 #9d6fff);
}

/* Input Fields */
QLineEdit {
    background-color: #000000;
    color: #E0E0E0;
    border: 1px solid #333333;
    padding: 8px;
    border-radius: 4px;
}

QLineEdit:focus {
    border: 1px solid #58a6ff;
    background-color: #000000;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #121212;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #424242;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #121212;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #424242;
    min-width: 20px;
    border-radius: 4px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ComboBox */
QComboBox {
    background-color: #000000;
    color: #E0E0E0;
    border: 1px solid #333333;
    padding: 6px 10px;
    border-radius: 4px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #505050;
}

QComboBox:focus {
    border-color: #58a6ff;
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
    background-color: #1E1E1E;
    border: 1px solid #333333;
    selection-background-color: #58a6ff;
    selection-color: #FFFFFF;
    padding: 4px;
    outline: none;
}

/* Slider */
QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #333333;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #58a6ff;
    border: none;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #8b5cf6;
}

QSlider::sub-page:horizontal {
    background: #58a6ff;
    border-radius: 2px;
}

/* TabWidget */
QTabWidget::pane {
    border: none;
    background-color: #1E1E1E;
}

QTabBar::tab {
    background: transparent;
    color: #8b9dc3;
    padding: 10px 20px;
    margin-right: 2px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}

QTabBar::tab:selected {
    color: #FFFFFF;
    border-bottom: 2px solid #58a6ff;
}

QTabBar::tab:hover:!selected {
    color: #c9d1d9;
}

/* CheckBox */
QCheckBox {
    spacing: 8px;
    color: #E0E0E0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3E3E3E;
    border-radius: 3px;
    background-color: #000000;
}

QCheckBox::indicator:hover {
    border-color: #505050;
}

QCheckBox::indicator:checked {
    background-color: #58a6ff;
    border-color: #58a6ff;
}

/* ProgressBar */
QProgressBar {
    border: none;
    border-radius: 4px;
    text-align: center;
    background-color: #333333;
    color: #FFFFFF;
    height: 6px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #58a6ff, stop:1 #8b5cf6);
    border-radius: 4px;
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
    background-color: #000000;
    color: #E0E0E0;
    border: 1px solid #333333;
    padding: 6px;
    border-radius: 4px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #58a6ff;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: transparent;
    border: none;
    width: 0;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: transparent;
    border: none;
    width: 0;
}
"""
