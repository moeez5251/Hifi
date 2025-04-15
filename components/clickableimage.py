from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Signal, Qt

class ClickableImage(QLabel):
    clicked = Signal(str)  # Emit the track ID when clicked

    def __init__(self, track_id="", parent=None):
        super().__init__(parent)
        self.track_id = track_id
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.clicked.emit(self.track_id)
