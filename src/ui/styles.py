
# Modern Dark Theme Palette (Tailwind-based)
COLORS = {
    "bg_main": "#0b0b0f",       # Main window background
    "bg_panel": "#18181c",      # Panels (Sidebar, Inspector)
    "bg_panel_2": "#202027",    # Elevated controls
    "bg_canvas": "#050507",     # Player, Media Grid
    "bg_timeline": "#101014",   # Timeline background
    "border": "#2c2c35",        # Borders/Dividers
    "border_soft": "#23232b",
    "text_primary": "#f4f4f5",
    "text_secondary": "#a7a7b2",
    "text_muted": "#71717a",
    "accent": "#6d5dfc",
    "accent_hover": "#7c6dff",
    "accent_soft": "rgba(109, 93, 252, 0.16)",
    "danger": "#ef4444",
    "scrollbar_track": "#141418",
    "scrollbar_thumb": "#4b4b58"
}

DARK_THEME = f"""
/* Global Reset */
QWidget {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_primary']};
    font-family: "Arial";
    font-size: 13px;
    selection-background-color: {COLORS['accent']};
    selection-color: #ffffff;
}}

/* --- Main Window & Panels --- */
QMainWindow {{
    background-color: {COLORS['bg_main']};
}}

QFrame#panel {{
    background-color: {COLORS['bg_panel']};
    border: none;
}}

QLabel#panel_title {{
    color: {COLORS['text_primary']};
    font-weight: 600;
    font-size: 12px;
    padding: 10px 14px;
    background-color: {COLORS['bg_panel']};
    border-bottom: 1px solid {COLORS['border']};
}}

/* --- Splitter --- */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* --- ScrollBar --- */
QScrollBar:vertical {{
    background: {COLORS['scrollbar_track']};
    width: 6px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['scrollbar_thumb']};
    min-height: 20px;
    border-radius: 3px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {COLORS['scrollbar_track']};
    height: 6px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['scrollbar_thumb']};
    min-width: 20px;
    border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* --- Buttons --- */
QPushButton {{
    background-color: {COLORS['bg_panel_2']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_primary']};
    padding: 7px 12px;
    border-radius: 7px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: #292936;
    border-color: #3a3a46;
}}
QPushButton:pressed {{
    background-color: #15151b;
}}
QPushButton:focus {{
    border: 1px solid {COLORS['accent_hover']};
}}
QPushButton#primary {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop:0 {COLORS['accent_hover']}, stop:1 #8b5cf6);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: white;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop:0 #877cff, stop:1 #a06cff);
}}
QPushButton#secondary {{
    background-color: #25252d;
    border: 1px solid #383844;
    color: {COLORS['text_primary']};
}}
QPushButton#ghost {{
    background-color: transparent;
    border: 1px solid transparent;
    color: {COLORS['text_secondary']};
}}
QPushButton#ghost:hover {{
    background-color: rgba(255, 255, 255, 0.06);
    color: {COLORS['text_primary']};
}}
QPushButton#danger {{
    background-color: {COLORS['danger']};
    color: white;
}}

/* --- Inputs (LineEdit, SpinBox) --- */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: #141419;
    border: 1px solid {COLORS['border']};
    border-radius: 7px;
    padding: 6px 9px;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent']};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {COLORS['accent_hover']};
    background-color: #181820;
}}
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    color: {COLORS['text_muted']};
    background-color: #111116;
}}

/* --- ComboBox --- */
QComboBox {{
    background-color: #141419;
    border: 1px solid {COLORS['border']};
    border-radius: 7px;
    padding: 6px 32px 6px 10px;
    min-height: 30px;
    color: {COLORS['text_primary']};
}}
QComboBox:focus {{
    border: 1px solid {COLORS['accent_hover']};
}}
QComboBox::drop-down {{
    width: 28px;
    border: none;
    border-left: 1px solid {COLORS['border_soft']};
    background: transparent;
}}
QComboBox::down-arrow {{
    width: 9px;
    height: 9px;
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent']};
    selection-color: #ffffff;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    outline: 0;
    padding: 6px;
    max-height: 280px;
}}
QComboBox QAbstractItemView::item {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    min-height: 28px;
    padding: 5px 10px;
    margin: 2px;
    border-radius: 6px;
    border: none;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: rgba(255, 255, 255, 0.05);
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {COLORS['accent']};
    color: #ffffff;
}}

/* --- Sliders --- */
QSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background: #32323c;
    margin: 2px 0;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {COLORS['accent']};
    border: 2px solid #c7d2fe;
    width: 13px;
    height: 13px;
    margin: -6px 0;
    border-radius: 7px;
}}

/* --- Tab Widget --- */
QTabWidget::pane {{
    border: none;
    background: {COLORS['bg_panel']};
}}
QTabBar::tab {{
    background: transparent;
    color: {COLORS['text_secondary']};
    padding: 10px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    color: {COLORS['accent_hover']};
    border-bottom: 2px solid {COLORS['accent']};
}}
QTabBar::tab:hover {{
    color: {COLORS['text_primary']};
}}

/* --- List Widget (Media Pool) --- */
QListWidget {{
    background-color: {COLORS['bg_panel']};
    border: none;
    outline: none;
}}
QListWidget::item {{
    color: {COLORS['text_primary']};
    border-radius: 7px;
    padding: 6px;
}}
QListWidget::item:selected {{
    background-color: {COLORS['accent_soft']};
    border: 1px solid {COLORS['accent']};
}}
QListWidget::item:hover {{
    background-color: rgba(255, 255, 255, 0.05);
}}

/* --- ToolTip --- */
QToolTip {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    padding: 4px;
}}
"""
