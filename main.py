import sys
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the current directory to sys.path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def smoke_native_core() -> int:
    import video_core

    transition_json = video_core.queue_transition_json(
        "pending",
        0,
        None,
        "running",
        25,
        None,
    )
    if '"status":"running"' not in transition_json:
        raise RuntimeError(f"Unexpected video_core smoke output: {transition_json}")
    print(f"video_core {video_core.version()} smoke ok")
    return 0


def main():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from src.ui.styles import DARK_THEME
    from src.ui.main_window import MainWindow
    from src.core.queue_manager import queue_manager
    from src.core.profiling import emit_profile_report

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    app.aboutToQuit.connect(queue_manager.shutdown)
    app.aboutToQuit.connect(emit_profile_report)
    
    # Set app icon for dock/taskbar
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    if "--smoke-native-core" in sys.argv:
        sys.exit(smoke_native_core())
    main()
