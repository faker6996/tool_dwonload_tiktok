DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
    color: #ffffff;
}
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}
/* Sidebar Styles */
QListWidget {
    background-color: #252526;
    border: none;
    outline: none;
    min-width: 180px;
    max-width: 180px;
}
QListWidget::item {
    padding: 15px 20px;
    color: #cccccc;
    border-left: 3px solid transparent;
}
QListWidget::item:selected {
    background-color: #37373d;
    color: #ffffff;
    border-left: 3px solid #007acc;
}
QListWidget::item:hover {
    background-color: #2a2d2e;
}

/* Input Styles */
QLineEdit {
    padding: 12px;
    border: 2px solid #333333;
    border-radius: 8px;
    background-color: #2d2d2d;
    color: #ffffff;
    selection-background-color: #007acc;
}
QLineEdit:focus {
    border: 2px solid #007acc;
}

/* Button Styles */
QPushButton {
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: bold;
    border: none;
}
QPushButton#primary {
    background-color: #007acc;
    color: white;
}
QPushButton#primary:hover {
    background-color: #005c99;
}
QPushButton#secondary {
    background-color: #333333;
    color: white;
}
QPushButton#secondary:hover {
    background-color: #444444;
}

/* Progress Bar */
QProgressBar {
    border: 2px solid #333333;
    border-radius: 5px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #007acc;
}

/* Labels */
QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #007acc;
    margin-bottom: 10px;
}
QLabel#page_title {
    font-size: 28px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 20px;
}

/* Preview Frame */
QFrame#preview_frame {
    border: 2px solid #333333;
    border-radius: 12px;
    background-color: #000000;
}
"""
