import sys
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the current directory to sys.path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.ui.styles import DARK_THEME
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    
    # Set app icon for dock/taskbar
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
