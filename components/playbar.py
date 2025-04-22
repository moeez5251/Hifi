from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSlider, QSizePolicy
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QRect, QTimer, QUrl, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import math
import requests
from components.playlist import get_audio_info_by_id

class AudioLoaderThread(QThread):
    """Thread to load audio info and thumbnail asynchronously"""
    data_loaded = Signal(dict)  # Signal to emit loaded data
    error_occurred = Signal(str)  # Signal to emit error message

    def __init__(self, video_id):
        super().__init__()
        self.video_id = video_id

    def run(self):
        """Run network operations in a separate thread"""
        try:
            # Fetch audio info
            audio_info = get_audio_info_by_id(self.video_id)
            audio_url = audio_info["audio_url"]
            track_name = audio_info["title"]
            artist_name = audio_info["artist"]
            thumbnail_url = audio_info["thumbnail"]

            # Fetch thumbnail
            response = requests.get(thumbnail_url)
            thumbnail_data = response.content

            # Emit loaded data
            self.data_loaded.emit({
                "audio_url": audio_url,
                "track_name": track_name,
                "artist_name": artist_name,
                "thumbnail_data": thumbnail_data
            })
        except Exception as e:
            self.error_occurred.emit(str(e))

class PlayBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("playbar")
        self.is_maximized = False
        self.is_playing = False
        self.normal_geometry = QRect(0, 0, self.width(), 80)
        
        # Audio setup
        self.audio = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio.setAudioOutput(self.audio_output)
        self.current_track_id = None
        
        # Timer for time updates
        self.time_update_timer = QTimer(self)
        self.time_update_timer.timeout.connect(self.update_time)

        # Timer for background animation
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_background_animation)
        self.animation_phase = 0.0
        self.secondary_phase = 0.0  # For secondary animation layer

        # Ensure the widget is opaque
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 10, 20, 10)
        self.main_layout.setSpacing(15)
        self.main_layout.setAlignment(Qt.AlignCenter)
       
        # Thumbnail label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setObjectName("thumbnail-label")
        self.thumbnail_label.setFixedSize(60, 60)  # Normal state: 60x60
        self.thumbnail_label.setScaledContents(True)
        self.main_layout.addWidget(self.thumbnail_label)

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
        self.seek_bar.valueChanged.connect(self.seek)
        self.audio.positionChanged.connect(self.update_position)
        self.audio.durationChanged.connect(self.update_duration)
        self.main_layout.addWidget(self.seek_bar)

        # Time label
        self.time_label = QLabel("0:00 / 0:00")
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
        thumbnail_size = 100 if is_maximized else 60  # Square thumbnail: 100x100 in maximized
        background = """
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #87CEEB, stop:1 #00B7EB);
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
                background: transparent;
            }}
            #artist-label {{
                color: #FFFFFF;
                font-size: {font_sizes['artist']}px;
                background: transparent;
            }}
            #time-label {{
                color: white;
                font-size: {font_sizes['time']}px;
                background: transparent;
            }}
            #thumbnail-label {{
                border: none;
                background: transparent;
                width: {thumbnail_size}px;
                height: {thumbnail_size}px;
            }}
        """)
        # Update thumbnail size dynamically
        self.thumbnail_label.setFixedSize(thumbnail_size, thumbnail_size)
        # Stop animation timer if maximized
        if is_maximized:
            self.animation_phase = 0.0
            self.secondary_phase = 0.0
            self.animation_timer.stop()
        elif self.is_playing:
            self.animation_timer.start(33)  # Update every 33ms for smoother animation (~30 FPS)

    def update_background_animation(self):
        """Update the background with a beat-like animation (only in non-maximized state)"""
        if self.is_maximized or not self.is_playing:
            self.animation_timer.stop()
            return

        self.animation_phase += 0.15  # Faster primary pulse
        self.secondary_phase += 0.08  # Slower secondary wave
        if self.animation_phase > 2 * math.pi:
            self.animation_phase -= 2 * math.pi
        if self.secondary_phase > 2 * math.pi:
            self.secondary_phase -= 2 * math.pi

        # Primary pulse (radial-like effect with color shift)
        pulse1 = (math.sin(self.animation_phase) + 1) / 2  # 0 to 1
        color_r = int(238 * pulse1 + 0 * (1 - pulse1))  # Shift between #EE10B0 and darker
        color_g = int(16 * pulse1 + 30 * (1 - pulse1))
        color_b = int(176 * pulse1 + 79 * (1 - pulse1))
        opacity1 = int(50 + pulse1 * 100)  # 50 to 150
        stop1 = pulse1 * 0.4 + 0.2  # 0.2 to 0.6
        stop2 = pulse1 * 0.4 + 0.5  # 0.5 to 0.9

        # Secondary wave (linear gradient for depth)
        wave = (math.sin(self.secondary_phase) + 1) / 2
        cyan_opacity = int(30 + wave * 70)  # 30 to 100
        wave_stop1 = wave * 0.3 + 0.3  # 0.3 to 0.6
        wave_stop2 = wave * 0.3 + 0.6  # 0.6 to 0.9

        # Combine radial and linear gradients with shadow effect
        animated_background = f"""
            background: qradialgradient(cx:0.5, cy:0.5, radius:0.8,
                stop:0 rgba({color_r}, {color_g}, {color_b}, {opacity1}),
                stop:{stop1:.2f} rgba(30, 30, 79, 100),
                stop:{stop2:.2f} rgba(59, 59, 79, 80)),
                qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(30, 30, 79, 80),
                stop:{wave_stop1:.2f} rgba(0, 255, 255, {cyan_opacity}),
                stop:{wave_stop2:.2f} rgba(0, 255, 255, {cyan_opacity}),
                stop:1 rgba(59, 59, 79, 80));
            border: none;
        """
        self.setStyleSheet(f"""
            #playbar {{
                {animated_background}
            }}
            #seek-bar {{
                height: 8px;
                background: #3B3B4F;
                border-radius: 4px;
                margin: 0 10px;
            }}
            #seek-bar::groove:horizontal {{
                background: #3B3B4F;
                border-radius: 4px;
            }}
            #seek-bar::handle:horizontal {{
                background: #EE10B0;
                border-radius: 6px;
                width: 12px;
                height: 12px;
                margin: -2px 0;
            }}
            #seek-bar::sub-page:horizontal {{
                background: #EE10B0;
                border-radius: 4px;
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
                font-size: 16px;
                background: transparent;
            }}
            #artist-label {{
                color: #FFFFFF;
                font-size: 14px;
                background: transparent;
            }}
            #time-label {{
                color: white;
                font-size: 14px;
                background: transparent;
            }}
            #thumbnail-label {{
                border: none;
                background: transparent;
            }}
        """)

    def format_time(self, seconds):
        """Format seconds into mm:ss"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def update_track_info(self, track_name, artist_name, duration):
        """Update the playbar with track information"""
        self.track_label.setText(track_name)
        self.artist_label.setText(artist_name)
        try:
            minutes, seconds = map(int, duration.split(":"))
            total_seconds = minutes * 60 + seconds
            self.seek_bar.setMaximum(total_seconds)
            self.time_label.setText(f"0:00 / {duration}")
        except:
            self.seek_bar.setMaximum(100)
            self.time_label.setText("0:00 / 0:00")

    def update_duration(self, duration):
        """Update seek bar maximum when duration is available"""
        if duration > 0:
            self.seek_bar.setMaximum(int(duration / 1000))  # Convert ms to seconds
            self.time_label.setText(f"0:00 / {self.format_time(duration / 1000)}")

    def update_position(self, position):
        """Update seek bar and time label with current position"""
        if not self.seek_bar.isSliderDown():
            current_time = position / 1000  # Convert ms to seconds
            self.seek_bar.setValue(int(current_time))
            duration = self.audio.duration() / 1000 if self.audio.duration() > 0 else 0
            self.time_label.setText(f"{self.format_time(current_time)} / {self.format_time(duration)}")

    def toggle_play(self):
        """Toggle between play and pause states"""
        if not self.audio.source().isValid():
            return
            
        self.is_playing = not self.is_playing
        icon = "assets/svgs/pause.svg" if self.is_playing else "assets/svgs/play.svg"
        self.play_button.setIcon(QIcon(icon))
        
        if self.is_playing:
            self.audio.play()
            self.time_update_timer.start(1000)  # Update every second
            if not self.is_maximized:
                self.animation_timer.start(33)  # Start background animation only if not maximized
        else:
            self.audio.pause()
            self.time_update_timer.stop()
            self.animation_timer.stop()  # Stop background animation
            self.update_stylesheet(self.is_maximized)  # Reset to static background

    def update_time(self):
        """Update the time label and seek bar position"""
        if self.audio.isAvailable() and not self.seek_bar.isSliderDown():
            current_time = self.audio.position() / 1000  # Convert ms to seconds
            duration = self.audio.duration() / 1000 if self.audio.duration() > 0 else 0
            self.seek_bar.setValue(int(current_time))
            self.time_label.setText(f"{self.format_time(current_time)} / {self.format_time(duration)}")

    def seek(self, value):
        """Seek to a specific position in the track"""
        if self.audio.isAvailable():
            self.audio.setPosition(value * 1000)  # Convert seconds to ms
            self.update_time()

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
        """Remove the playbar and stop playback"""
        # Stop audio
        if self.audio:
            self.audio.stop()
            self.audio.setSource(QUrl())  # Clear source
            self.time_update_timer.stop()
            self.animation_timer.stop()
        
        # Disconnect any signals to prevent further interactions
        try:
            self.play_button.clicked.disconnect()
            self.toggle_button.clicked.disconnect()
            self.close_button.clicked.disconnect()
            self.seek_bar.valueChanged.disconnect()
            self.audio.positionChanged.disconnect()
            self.audio.durationChanged.disconnect()
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

    def play_track(self, video_id):
        """Play a track by its YouTube video ID"""
        if self.current_track_id == video_id and self.audio:
            if not self.is_playing:
                self.toggle_play()
            return

        # Show loading state
        self.track_label.setText("Loading...")
        self.thumbnail_label.clear()

        # Stop and clean up existing audio
        if self.audio:
            self.audio.stop()
            self.audio.setSource(QUrl())
            self.time_update_timer.stop()
            self.seek_bar.setValue(0)
            self.time_label.setText("0:00 / 0:00")

        self.current_track_id = video_id

        # Start thread to load audio info and thumbnail
        self.loader_thread = AudioLoaderThread(video_id)
        self.loader_thread.data_loaded.connect(self.on_audio_data_loaded)
        self.loader_thread.error_occurred.connect(self.on_audio_load_error)
        self.loader_thread.start()

    def on_audio_data_loaded(self, data):
        """Handle loaded audio data from thread"""
        try:
            # Update track information
            self.update_track_info(data["track_name"], data["artist_name"], "0:00")

            # Load and set thumbnail
            pixmap = QPixmap()
            pixmap.loadFromData(data["thumbnail_data"])
            thumbnail_size = 100 if self.is_maximized else 60
            self.thumbnail_label.setPixmap(pixmap.scaled(thumbnail_size, thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            # Set and play the audio
            self.audio.setSource(QUrl(data["audio_url"]))
            self.audio.play()
            self.is_playing = True
            self.play_button.setIcon(QIcon("assets/svgs/pause.svg"))
            self.time_update_timer.start(1000)
            if not self.is_maximized:
                self.animation_timer.start(33)  # Start background animation only if not maximized
        except Exception as e:
            self.track_label.setText("Error loading track")
            self.audio.setSource(QUrl())
            self.thumbnail_label.clear()

    def on_audio_load_error(self, error):
        """Handle errors from audio loading thread"""
        self.track_label.setText("Error loading track")
        self.audio.setSource(QUrl())
        self.thumbnail_label.clear()