
# Modern Dark Theme Palette (Tailwind-based)
COLORS = {
    "bg_main": "#0f0f10",       # Main window background
    "bg_panel": "#18181b",      # Panels (Sidebar, Inspector)
    "bg_canvas": "#09090b",     # Player, Media Grid
    "bg_timeline": "#131315",   # Timeline background
    "border": "#27272a",        # Borders/Dividers
    "text_primary": "#e5e5e5",
    "text_secondary": "#a1a1aa",
    "accent": "#4f46e5",        # Indigo-600
    "accent_hover": "#6366f1",  # Indigo-500
    "danger": "#ef4444",
    "scrollbar_track": "#18181b",
    "scrollbar_thumb": "#3f3f46"
}

DARK_THEME = f"""
/* Global Reset */
QWidget {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_primary']};
    font-family: "Segoe UI", "Inter", sans-serif;
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
    padding: 8px 12px;
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
    background-color: transparent;
    border: none;
    color: {COLORS['text_primary']};
    padding: 6px 12px;
    border-radius: 4px;
}}
QPushButton:hover {{
    background-color: rgba(255, 255, 255, 0.05);
}}
QPushButton#primary {{
    background-color: {COLORS['accent']};
    color: white;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background-color: {COLORS['accent_hover']};
}}
QPushButton#danger {{
    background-color: {COLORS['danger']};
    color: white;
}}

/* --- Inputs (LineEdit, SpinBox) --- */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_canvas']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 8px;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent']};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {COLORS['accent']};
}}

/* --- ComboBox --- */
QComboBox {{
    background-color: {COLORS['bg_canvas']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 28px;
    color: {COLORS['text_primary']};
}}
QComboBox:focus {{
    border: 1px solid {COLORS['accent']};
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent']};
    selection-color: #ffffff;
    border: 1px solid {COLORS['border']};
    outline: 0;
    padding: 4px 0;
}}
QComboBox::item {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_primary']};
    padding: 6px 10px;
    min-height: 24px;
}}
QComboBox::item:selected {{
    background-color: {COLORS['accent']};
    color: #ffffff;
}}

/* --- Sliders --- */
QSlider::groove:horizontal {{
    border: 1px solid {COLORS['border']};
    height: 4px;
    background: {COLORS['border']};
    margin: 2px 0;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
    width: 12px;
    height: 12px;
    margin: -5px 0;
    border-radius: 6px;
}}

/* --- Tab Widget --- */
QTabWidget::pane {{
    border: none;
    background: {COLORS['bg_panel']};
}}
QTabBar::tab {{
    background: transparent;
    color: {COLORS['text_secondary']};
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    color: {COLORS['accent']};
    border-bottom: 2px solid {COLORS['accent']};
}}
QTabBar::tab:hover {{
    color: {COLORS['text_primary']};
}}

/* --- List Widget (Media Pool) --- */
QListWidget {{
    background-color: {COLORS['bg_canvas']};
    border: none;
    outline: none;
}}
QListWidget::item {{
    color: {COLORS['text_primary']};
    border-radius: 4px;
    padding: 4px;
}}
QListWidget::item:selected {{
    background-color: rgba(79, 70, 229, 0.2);
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
