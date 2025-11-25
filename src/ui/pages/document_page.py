from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser
from PyQt6.QtCore import Qt

class DocumentPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Supported Platforms")
        title.setObjectName("page_title")
        layout.addWidget(title)
        
        content = QTextBrowser()
        content.setOpenExternalLinks(True)
        content.setStyleSheet("border: none; background-color: transparent; color: #cccccc; font-size: 15px;")
        content.setHtml("""
            <h3 style="color: #007acc;">✅ Fully Supported</h3>
            <ul>
                <li><b>TikTok</b>: No watermark, supports private videos (with cookies).</li>
                <li><b>Douyin</b>: No watermark, auto-handling of some captchas.</li>
                <li><b>YouTube</b>: Supports Videos, Shorts, and Live streams.</li>
                <li><b>Threads</b>: Supports video downloads.</li>
            </ul>
            
            <h3 style="color: #e6b800;">⚠️ Basic Support</h3>
            <p>The following platforms are supported but may require cookies or have limitations due to strict anti-bot measures:</p>
            <ul>
                <li><b>Facebook</b> (Watch, Reels)</li>
                <li><b>Instagram</b> (Reels, Stories)</li>
                <li><b>X (Twitter)</b></li>
            </ul>
            
            <hr>
            <p><i>Note: For "Basic Support" platforms, if a download fails, try pasting the link again or check if the video is public.</i></p>
        """)
        layout.addWidget(content)
