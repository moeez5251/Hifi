# components/player_web.py

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
import os

class PlayerWeb(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.webview = QWebEngineView()
        layout.addWidget(self.webview)

    def play_track(self, track_id):
        html = f"""
        <html>
        <body style="margin:0;">
            <iframe src="https://open.spotify.com/embed/track/{track_id}?utm_source=generator"
                width="100%" height="80" frameborder="0" allowtransparency="true"
                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                loading="lazy"></iframe>
        </body>
        </html>
        """
        path = os.path.abspath("components/player.html")
        with open(path, "w") as file:
            file.write(html)
        self.webview.load(f"file:///{path}")
