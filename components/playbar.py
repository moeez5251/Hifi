from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSlider,QSizePolicy
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QRect
from PySide6.QtGui import QIcon

class PlayBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("playbar")
        self.is_maximized = False
        self.is_playing = False
        self.normal_geometry = QRect(0, 0, self.width(), 80)

        # Ensure the widget is opaque
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 10, 20, 10)
        self.main_layout.setSpacing(15)
        self.main_layout.setAlignment(Qt.AlignCenter)
       
        # Play/Pause button
        self.play_button = QPushButton()
        self.play_button.setObjectName("play-button")
        self.play_button.setIcon(QIcon("assets/svgs/play.svg"))
        self.play_button.setIconSize(QSize(24, 24))
        self.play_button.setFixedSize(40, 40)
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.clicked.connect(self.toggle_play)
        self.main_layout.addWidget(self.play_button)

        # Track label
        self.track_label = QLabel("No track playing")
        self.track_label.setObjectName("track-label")
        self.track_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.track_label.setMaximumHeight(30)
        self.main_layout.addWidget(self.track_label)

        # Artist label
        self.artist_label = QLabel("")
        self.artist_label.setObjectName("artist-label")
        self.artist_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.artist_label.setMaximumHeight(25)
        self.main_layout.addWidget(self.artist_label)

        # Seek bar
        self.seek_bar = QSlider(Qt.Horizontal)
        self.seek_bar.setObjectName("seek-bar")
        self.seek_bar.setMinimum(0)
        self.seek_bar.setMaximum(100)
        self.seek_bar.setValue(0)
        self.seek_bar.setFixedWidth(200)
        self.seek_bar.setCursor(Qt.PointingHandCursor)
        self.main_layout.addWidget(self.seek_bar)

        # Time label
        self.time_label = QLabel("0:00")
        self.time_label.setObjectName("time-label")
        self.time_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.time_label.setMaximumHeight(25)
        self.main_layout.addWidget(self.time_label)

        # Maximize/Minimize button
        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("toggle-button")
        self.toggle_button.setIcon(QIcon("assets/svgs/maximize.svg"))
        self.toggle_button.setIconSize(QSize(24, 24))
        self.toggle_button.setFixedSize(40, 40)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.clicked.connect(self.toggle_maximize)
        self.main_layout.addWidget(self.toggle_button)

        # Close button
        self.close_button = QPushButton()
        self.close_button.setObjectName("close-button")
        self.close_button.setIcon(QIcon("assets/svgs/close.svg"))
        self.close_button.setIconSize(QSize(24, 24))
        self.close_button.setFixedSize(40, 40)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.clicked.connect(self.close_player)
        self.main_layout.addWidget(self.close_button)

        # Animation setup
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)

        # Initial stylesheet
        self.update_stylesheet(False)

    def update_stylesheet(self, is_maximized):
        """Update stylesheet based on maximized state"""
        font_sizes = {
            "track": 24 if is_maximized else 16,
            "artist": 18 if is_maximized else 14,
            "time": 16 if is_maximized else 14
        }
        background = """
            background: #000000;
        """ if is_maximized else """
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1E1E2F, stop:0.5 #EE10B0, stop:1 #3B3B4F);
        """
        self.setStyleSheet(f"""
            #playbar {{
                {background}
                border: {'' if is_maximized else '1px solid #3B3B4F'};
            }}
            #seek-bar {{
                height: {10 if is_maximized else 8}px;
                background: #3B3B4F;
                border-radius: {5 if is_maximized else 4}px;
                margin: 0 10px;
            }}
            #seek-bar::groove:horizontal {{
                background: #3B3B4F;
                border-radius: {5 if is_maximized else 4}px;
            }}
            #seek-bar::handle:horizontal {{
                background: #EE10B0;
                border-radius: {8 if is_maximized else 6}px;
                width: {16 if is_maximized else 12}px;
                height: {16 if is_maximized else 12}px;
                margin: {-3 if is_maximized else -2}px 0;
            }}
            #seek-bar::sub-page:horizontal {{
                background: #EE10B0;
                border-radius: {5 if is_maximized else 4}px;
            }}
            #play-button, #toggle-button, #close-button {{
                background: transparent;
                border: none;
            }}
            #play-button:hover, #toggle-button:hover, #close-button:hover {{
                background: #3B3B4F;
                border-radius: 20px;
            }}
            #track-label {{
                color: #FFFFFF;
                font-weight: bold;
                font-size: {font_sizes['track']}px;
                padding: 5px;
                border-radius: 5px;
            }}
            #artist-label {{
                color: #B0B0C0;
                font-size: {font_sizes['artist']}px;
                padding: 5px;
                border-radius: 5px;
            }}
            #time-label {{
                color: #EE10B0;
                font-size: {font_sizes['time']}px;
                padding: 5px;
                border-radius: 5px;
            }}
        """)

    def update_track_info(self, track_name, artist_name, duration):
        """Update the playbar with track information"""
        self.track_label.setText(track_name)
        self.artist_label.setText(artist_name)
        self.time_label.setText(duration)
        try:
            minutes, seconds = map(int, duration.split(":"))
            total_seconds = minutes * 60 + seconds
            self.seek_bar.setMaximum(total_seconds)
        except:
            self.seek_bar.setMaximum(100)

    def toggle_play(self):
        """Toggle between play and pause states"""
        self.is_playing = not self.is_playing
        icon = "assets/svgs/pause.svg" if self.is_playing else "assets/svgs/play.svg"
        self.play_button.setIcon(QIcon(icon))

    def toggle_maximize(self):
        """Toggle between normal and full-screen states with animation"""
        self.is_maximized = not self.is_maximized
        parent = self.parent()

        if self.is_maximized:
            self.normal_geometry = self.geometry()
            full_geometry = parent.geometry() if parent else QRect(0, 0, 1000, 1000)
            self.animation.setStartValue(self.normal_geometry)
            self.animation.setEndValue(full_geometry)
            self.raise_()
            self.seek_bar.setFixedWidth(400)
            self.update_stylesheet(True)
        else:
            self.animation.setStartValue(self.geometry())
            self.animation.setEndValue(self.normal_geometry)
            self.lower()
            self.seek_bar.setFixedWidth(200)
            self.update_stylesheet(False)

        icon = "assets/svgs/minimize.svg" if self.is_maximized else "assets/svgs/maximize.svg"
        self.toggle_button.setIcon(QIcon(icon))
        self.animation.start()

    def close_player(self):
        """Remove the playbar"""
        # Disconnect any signals to prevent further interactions
        try:
            self.play_button.clicked.disconnect()
            self.toggle_button.clicked.disconnect()
            self.close_button.clicked.disconnect()
        except:
            pass  # Ignore if signals are already disconnected
        
        # Remove from layout and schedule deletion
        if self.parent():
            self.setParent(None)  # Detach from parent to remove from layout
        self.deleteLater()  # Schedule deletion

    def resizeEvent(self, event):
        """Ensure playbar covers the entire parent in full-screen mode"""
        if self.is_maximized:
            parent = self.parent()
            if parent:
                self.setGeometry(parent.geometry())
        super().resizeEvent(event)
    def play_track(self, track_id):
        self.player_web.play_track(track_id)
