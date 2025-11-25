DARK_THEME = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0a0e27, stop:1 #1a1f3a);
    color: #ffffff;
}
QWidget {
    background-color: transparent;
    color: #ffffff;
    font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
    font-size: 14px;
}

/* Sidebar Styles - Modern Glassmorphism */
QWidget#sidebar_container {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(26, 31, 58, 0.95), 
                                stop:1 rgba(15, 18, 35, 0.95));
    border-right: 1px solid rgba(88, 166, 255, 0.2);
}

QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
    min-width: 200px;
    max-width: 200px;
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

/* Input Styles - Modern with Glow */
QLineEdit {
    padding: 12px 16px;
    border: 2px solid rgba(88, 166, 255, 0.3);
    border-radius: 10px;
    background: rgba(22, 27, 34, 0.6);
    color: #ffffff;
    selection-background-color: #58a6ff;
    font-size: 14px;
}

QLineEdit:focus {
    border: 2px solid #58a6ff;
    background: rgba(22, 27, 34, 0.8);
}

QLineEdit::placeholder {
    color: rgba(139, 157, 195, 0.6);
}

/* Button Styles - Modern Gradient */
QPushButton {
    padding: 12px 28px;
    border-radius: 10px;
    font-weight: 600;
    border: none;
    font-size: 14px;
}

QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #58a6ff, stop:1 #8b5cf6);
    color: white;
}

QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #4a8fd9, stop:1 #7645d9);
}

QPushButton#primary:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #3d78b8, stop:1 #6237b8);
}

QPushButton#secondary {
    background: rgba(88, 166, 255, 0.1);
    color: #58a6ff;
    border: 1px solid rgba(88, 166, 255, 0.3);
}

QPushButton#secondary:hover {
    background: rgba(88, 166, 255, 0.2);
}

/* Progress Bar - Modern Gradient */
QProgressBar {
    border: none;
    border-radius: 6px;
    text-align: center;
    background: rgba(22, 27, 34, 0.6);
    height: 8px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #58a6ff, stop:1 #8b5cf6);
    border-radius: 6px;
}

/* Labels */
QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 10px;
}

QLabel#page_title {
    font-size: 32px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 20px;
    letter-spacing: -0.5px;
}

/* Preview Frame - Modern Card */
QFrame#preview_frame {
    border: 2px solid rgba(88, 166, 255, 0.2);
    border-radius: 16px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 rgba(22, 27, 34, 0.4), 
                                stop:1 rgba(10, 14, 39, 0.6));
}

/* Modern Card Style */
QWidget#content_card {
    background: rgba(22, 27, 34, 0.4);
    border-radius: 16px;
    border: 1px solid rgba(88, 166, 255, 0.1);
}
"""
