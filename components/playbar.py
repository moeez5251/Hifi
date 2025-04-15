from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize

class PlayBar(QWidget):
    def __init__(self, track_name, artist, parent=None):
        super().__init__(parent)
        self.expanded = False  # Track state

        self.track_name = track_name
        self.artist = artist

        self.setFixedHeight(80)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(15, 10, 15, 10)

        # Track info
        text_layout = QVBoxLayout()
        self.track_label = QLabel(track_name)
        self.artist_label = QLabel(artist)
        self.track_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.artist_label.setStyleSheet("font-size: 12px; color: gray;")
        text_layout.addWidget(self.track_label)
        text_layout.addWidget(self.artist_label)

        # Play button
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(40, 40)
        self.play_button.setCursor(Qt.PointingHandCursor)

        # Expand button
        self.expand_button = QPushButton("⤢")
        self.expand_button.setFixedSize(40, 40)
        self.expand_button.setCursor(Qt.PointingHandCursor)
        self.expand_button.clicked.connect(self.toggle_expand)

        # Right side buttons
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.play_button)
        right_layout.addWidget(self.expand_button)

        self.main_layout.addLayout(text_layout)
        self.main_layout.addStretch()
        self.main_layout.addLayout(right_layout)

        self.setLayout(self.main_layout)

    def toggle_expand(self):
        if not self.expanded:
            self.setStyleSheet("background-color: #121212; color: white;")
            self.setFixedHeight(self.parent().height())  # Fill parent height
            self.main_layout.setAlignment(Qt.AlignCenter)
            self.track_label.setStyleSheet("font-size: 24px; font-weight: bold;")
            self.artist_label.setStyleSheet("font-size: 18px; color: gray;")
            self.expand_button.setText("⤡")  # Collapse icon
            self.expanded = True
        else:
            self.setStyleSheet("background-color: #1e1e1e; color: white;")
            self.setFixedHeight(80)
            self.main_layout.setAlignment(Qt.AlignLeft)
            self.track_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            self.artist_label.setStyleSheet("font-size: 12px; color: gray;")
            self.expand_button.setText("⤢")
            self.expanded = False
