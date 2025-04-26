from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QScrollArea, QSizePolicy, QLineEdit
)
import sys
from PySide6.QtCore import Qt, QSize, QFile, QTextStream, QThread, Signal, QEvent, QTimer, QPropertyAnimation
from PySide6.QtGui import QIcon, QFontDatabase, QFont, QColor, QImage, QPixmap, QPainter, QPainterPath, QTransform, QPen
from components.gradient_label import GradientLabel
from components.playlist import search_youtube
from components.recognizer import AudioRecognizer
from io import BytesIO
from components.clickableimage import ClickableImage
from components.playbar import PlayBar
import requests

# Thread for fetching search results
class SearchWorker(QThread):
    results_fetched = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, query, max_results):
        super().__init__()
        self.query = query
        self.max_results = max_results

    def run(self):
        try:
            tracks = search_youtube(self.query, self.max_results)
            track_info = []
            for track in tracks:
                track_name = track['title'][:30]
                track_artists = track["name"][:30]
                track_image_url = track["thumbnail"]
                url = track['video_id']
                track_info.append({
                    "name": track_name,
                    "artists": track_artists,
                    "album_image": track_image_url,
                    "url": url
                })
            self.results_fetched.emit(track_info)
        except Exception as e:
            self.error_occurred.emit(str(e))

# Thread for audio recognition
class RecognitionWorker(QThread):
    recognition_finished = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, duration):
        super().__init__()
        self.duration = duration
        self.recognizer = None

    def run(self):
        try:
            self.recognizer = AudioRecognizer(self.duration)
            result = self.recognizer.process_audio()
            self.recognition_finished.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def cleanup(self):
        if self.recognizer:
            self.recognizer.clean_up()
            self.recognizer = None

# Animated Circle Widget
class AnimatedCircle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.angle = 0
        self.beat_amplitude = 0
        self.is_recognizing = False
        
        # Animation for beat effect
        self.beat_timer = QTimer(self)
        self.beat_timer.timeout.connect(self.update_beat)
        self.beat_timer.start(50)  # Update every 50ms
        
        # Animation for rotation
        self.rotation_animation = QPropertyAnimation(self, b"rotation_angle")
        self.rotation_animation.setDuration(10000)  # 10 seconds for one rotation
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)  # Infinite loop
        self.rotation_animation.start()

    def set_rotation_angle(self, angle):
        self.angle = angle
        self.update()

    def get_rotation_angle(self):
        return self.angle

    rotation_angle = property(get_rotation_angle, set_rotation_angle)

    def update_beat(self):
        if self.is_recognizing:
            self.beat_amplitude = (self.beat_amplitude + 0.2) % 1
        else:
            self.beat_amplitude = max(0, self.beat_amplitude - 0.1)
        self.update()

    def start_recognition(self):
        self.is_recognizing = True

    def stop_recognition(self):
        self.is_recognizing = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Center and size calculations
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 20
        
        # Draw background circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(40, 40, 40))
        painter.drawEllipse(center, radius, radius)
        
        # Draw "HiFi" text
        painter.setPen(Qt.white)
        font = QFont("Poppins", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "HiFi")
        
        # Draw animated beat bars
        num_bars = 60
        bar_width = 3
        max_bar_height = 20
        
        painter.translate(center)
        painter.rotate(self.angle)
        
        for i in range(num_bars):
            # Calculate color gradient (blue to pink to orange)
            hue = (i * 360 / num_bars) % 360
            color = QColor.fromHsv(hue, 255, 255)
            painter.setPen(QPen(color, bar_width))
            
            # Calculate bar height with beat animation
            base_height = 5
            beat_height = max_bar_height * self.beat_amplitude * (1 - abs((i % 15) - 7.5) / 7.5)
            height = base_height + beat_height
            
            # Draw bar
            painter.drawLine(0, radius, 0, radius + height)
            painter.rotate(360 / num_bars)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        font_id = QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            custom_font = QFont(font_family, 14)
            self.setFont(custom_font)
        self.setWindowTitle("HiFi")
        self.setMinimumSize(1000, 1000)
        self.setWindowIcon(QIcon("assets/Logo.png"))    
        self.load_stylesheet("style.css")
        
        # Main layout
        main_layout = QVBoxLayout(self)  # Use QVBoxLayout for playbar at bottom
        
        # Content layout (sidebar + pages)
        content_layout = QHBoxLayout()

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.setSpacing(10)  # Reduced spacing for tighter layout
        sidebar.setAlignment(Qt.AlignTop)
        sidebar.setContentsMargins(15, 15, 15, 0)  # Consistent margins

        # Logo
        self.head = GradientLabel("HiFi", font_size=25)
        self.head.setObjectName("label")
        sidebar.addWidget(self.head)
        
        # Menu label
        self.menu = QLabel("Menu")
        self.menu.setObjectName("Menu")
        sidebar.addWidget(self.menu)
        
        # Buttons
        self.home_button = QPushButton("Home")
        self.home_button.setIcon(QIcon("assets/svgs/home.svg"))
        self.home_button.setIconSize(QSize(20, 20))
        self.home_button.setObjectName("active-btn")
        self.search_button = QPushButton("Discover")
        self.search_button.setIcon(QIcon("assets/svgs/search.svg"))
        self.search_button.setIconSize(QSize(20, 20))
        self.recognize = QPushButton("Recognize")
        self.recognize.setIcon(QIcon("assets/svgs/recognize.svg"))
        self.recognize.setIconSize(QSize(20, 20))
        self.artist = QPushButton("Artist")
        self.artist.setIcon(QIcon("assets/svgs/Artist.svg"))
        self.artist.setIconSize(QSize(20, 20))
        for btn in [self.home_button, self.search_button, self.recognize, self.artist]:
            sidebar.addWidget(btn)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)  # Consistent height for padding

        # Recently Played label
        self.recentlyplayed = QLabel("Recently Played")
        self.recentlyplayed.setObjectName("recent")
        sidebar.addWidget(self.recentlyplayed)
        
        # Recently Played Buttons
        self.added = QPushButton("Recently Played")
        self.added.setIcon(QIcon("assets/svgs/time.svg"))
        self.added.setIconSize(QSize(20, 20))
        self.added.setCursor(Qt.PointingHandCursor)
        self.added.setFixedHeight(40)
        sidebar.addWidget(self.added)
        self.played = QPushButton("Most Played")
        self.played.setIcon(QIcon("assets/svgs/replay.svg"))
        self.played.setIconSize(QSize(20, 20))
        self.played.setCursor(Qt.PointingHandCursor)
        self.played.setFixedHeight(40)
        sidebar.addWidget(self.played)
        
        # General label
        self.recentlyplayed = QLabel("General")
        self.recentlyplayed.setObjectName("recent")
        sidebar.addWidget(self.recentlyplayed)
        
        # Logout button
        self.log = QPushButton("Logout")
        self.log.setIcon(QIcon("assets/svgs/logout.svg"))
        self.log.setIconSize(QSize(20, 20))
        self.log.setCursor(Qt.PointingHandCursor)
        self.log.setFixedHeight(40)
        sidebar.addWidget(self.log)
        
        # About Us
        sidebar.about = QLabel("About Us")
        sidebar.about.setObjectName("recent")
        sidebar.addWidget(sidebar.about)
        self.aboutbtn = QPushButton("About Us")
        self.aboutbtn.setIcon(QIcon("assets/svgs/about.svg"))
        self.aboutbtn.setIconSize(QSize(20, 20))
        self.aboutbtn.setCursor(Qt.PointingHandCursor)
        self.aboutbtn.setFixedHeight(40)
        sidebar.addWidget(self.aboutbtn)
        
        # Sidebar widget
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(200)  # Slightly wider for better padding
        sidebar_widget.setObjectName("sidebar")

        # Pages
        self.pages = QStackedWidget()

        # Home page
        home = QVBoxLayout()
        home.setSpacing(20)
        home.setAlignment(Qt.AlignTop)
        home.setContentsMargins(2, 0, 2, 0)

        # Background image
        background_label = QLabel()
        image = QImage('assets/Banner.png')
        if image.isNull():
            background_label.setStyleSheet("background: red;")
        else:
            transform = QTransform().scale(-1, 1)
            mirrored_image = image.transformed(transform, Qt.SmoothTransformation)
            window_width = self.width() if self.width() > 0 else 800
            image_height = int(self.height() * 0.5) if self.height() > 0 else 400

            scaled_pixmap = QPixmap.fromImage(mirrored_image).scaled(
                window_width, image_height,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

            final_pixmap = QPixmap(window_width, image_height)
            final_pixmap.fill(Qt.transparent)
            painter = QPainter(final_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            radius = 10
            path.addRoundedRect(0, 0, window_width, image_height, radius, radius)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled_pixmap)
            overlay_color = QColor(0, 0, 0, 100)
            painter.fillRect(final_pixmap.rect(), overlay_color)
            painter.end()

            background_label.setPixmap(final_pixmap)
            background_label.setScaledContents(True)

        # Content on background
        content_layout_background = QVBoxLayout(background_label)
        content_layout_background.setContentsMargins(20, 120, 0, 0)
        content_layout_background.setAlignment(Qt.AlignTop)
        content_layout_background.setSpacing(0)

        label1 = QLabel()
        label1.setObjectName("label1")
        label1.setText('<span style="font-weight: bold;">All the <span style="color: #EE10B0;">Best Songs</span> <br> in One Place</span>')
        content_layout_background.addWidget(label1)

        label2 = QLabel()
        label2.setText('<span>On our app, you can access an amazing collection of popular and new songs</span> <br> <span>Stream your favorite tracks in high quality and enjoy without interruptions </span> <br> <span> Whatever your taste in music, we have it all for you! </span>')
        label2.setObjectName("label2")
        content_layout_background.addWidget(label2)

        button = QPushButton("Discover Now")
        button.setCursor(Qt.PointingHandCursor)
        button.setObjectName("discover")
        button.setMaximumWidth(150)
        button.setFixedHeight(60)
        content_layout_background.addWidget(button)
 
        home.addWidget(background_label)

        below_label = QLabel()
        below_label.setText('<span>Weekly Top</span> <span style="color: #EE10B0;">Songs</span>')
        below_label.setObjectName("below-label")
        home.addWidget(below_label)

        # Tracks Layout
        self.main_track_layout = QHBoxLayout()
        self.main_track_layout.setContentsMargins(10, 10, 10, 10)
        
        # Store playbar instance
        self.playbar = None
        def on_image_click(track_url, track_name, artist_name):
            if self.playbar is not None:
                try:
                    self.playbar.close_player()  # Call close_player to hide and delete
                except RuntimeError:
                    pass
                self.playbar = None  # Clear the reference

            # Create a new playbar
            self.playbar = PlayBar(self)  # Pass self as parent
            main_layout.addWidget(self.playbar)  # Add to the main layout
            self.playbar.update_track_info(track_name, artist_name, "3:45")
            self.playbar.play_track(track_url)  # Pass the track URL to play

        try:
            tracks = search_youtube("Coke Studio", 25)
            track_info = []
            for track in tracks:
                track_name = track['title'][:30]
                track_artists = track["name"][:30]
                track_image_url = track["thumbnail"]
                href = track['video_id']
                url = track['video_id']
                track_info.append({
                    "name": track_name,
                    "artists": track_artists,
                    "album_image": track_image_url,
                    "href": href,
                    "url": url
                })
            for tr in track_info[2:7]:
                main_child_layout = QVBoxLayout()
                main_child_layout.setContentsMargins(0, 0, 0, 0)
                main_child_layout.setAlignment(Qt.AlignCenter)
                main_child_layout.setSpacing(10)
                image = ClickableImage(track_id=tr["url"])
                image_url = tr["album_image"]
                response = requests.get(image_url)
                response.raise_for_status()
                image_data = BytesIO(response.content)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data.read())
                pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

                rounded_pixmap = QPixmap(140, 150)
                rounded_pixmap.fill(Qt.transparent)
                painter = QPainter(rounded_pixmap)
                path = QPainterPath()
                path.addRoundedRect(0, 0, 140, 150, 10, 10)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                image.setPixmap(rounded_pixmap)
                image.setCursor(Qt.PointingHandCursor)
                image.setAlignment(Qt.AlignCenter)
                image.setObjectName("image-weekly")
                image.clicked.connect(lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]: on_image_click(turl, tname, tartist))
                main_child_layout.addWidget(image)
                label_name = QLabel(tr["name"])
                label_name.setObjectName("label-name")
                label_name.setAlignment(Qt.AlignCenter)
                label_name.setWordWrap(True)
                label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                main_child_layout.addWidget(label_name)
                label_name = QLabel(tr["artists"])
                label_name.setObjectName("artist-name")
                label_name.setAlignment(Qt.AlignCenter)
                main_child_layout.addWidget(label_name)

                self.main_track_layout.addLayout(main_child_layout)
            button_view = QPushButton("Show More")
            button_view.setIcon(QIcon("assets/svgs/more.svg"))
            button_view.setCursor(Qt.PointingHandCursor)
            button_view.setObjectName("button-view")
            button_view.setIconSize(QSize(40, 40))
            self.main_track_layout.addWidget(button_view)
        except Exception as e:
            not_label = QLabel("No Playlist Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.main_track_layout.addWidget(not_label)

        home.addLayout(self.main_track_layout)
        homepage_widget = QWidget()
        homepage_widget.setLayout(home)
        homepage_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        home_scroll_area = QScrollArea()
        home_scroll_area.setWidget(homepage_widget)
        home_scroll_area.setWidgetResizable(True)
        home_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        home_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        home_scroll_area.setStyleSheet("QScrollArea { border: none; }")

        self.pages.addWidget(home_scroll_area)
        
        # Weekly More
        self.weekly_more = QVBoxLayout()
        self.weekly_more.setSpacing(20)
        self.weekly_more.setAlignment(Qt.AlignTop)
        self.weekly_more.setContentsMargins(2, 0, 2, 0)
        
        below_label = QLabel()
        below_label.setText('<span endlessly>Weekly Top</span> <span style="color: #EE10B0;">Songs</span>')
        below_label.setObjectName("below-label")
        self.weekly_more.addWidget(below_label)
        self.song_layout = QHBoxLayout()
        self.song_layout.setContentsMargins(10, 10, 10, 10)
        for tr in track_info[0:5]:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            image = ClickableImage(track_id=tr["url"])
            image_url = tr["album_image"]
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.read())
            pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            rounded_pixmap = QPixmap(140, 150)
            rounded_pixmap.fill(Qt.transparent)
            painter = QPainter(rounded_pixmap)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 140, 150, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            image.setPixmap(rounded_pixmap)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]: on_image_click(turl, tname, tartist))
            main_child_layout.addWidget(image)
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            label_name = QLabel(tr["artists"])
            label_name.setObjectName("artist-name")
            label_name.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_name)
            self.song_layout.addLayout(main_child_layout)

        self.weekly_more.addLayout(self.song_layout)
        self.song_layout = QHBoxLayout()
        self.song_layout.setContentsMargins(10, 10, 10, 10)
        for tr in track_info[6:11]:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            image = ClickableImage(track_id=tr["url"])
            image_url = tr["album_image"]
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.read())
            pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            rounded_pixmap = QPixmap(140, 150)
            rounded_pixmap.fill(Qt.transparent)
            painter = QPainter(rounded_pixmap)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 140, 150, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            image.setPixmap(rounded_pixmap)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]: on_image_click(turl, tname, tartist))
            main_child_layout.addWidget(image)
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            label_name = QLabel(tr["artists"])
            label_name.setObjectName("artist-name")
            label_name.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_name)
            self.song_layout.addLayout(main_child_layout)

        self.weekly_more.addLayout(self.song_layout)
        self.song_layout = QHBoxLayout()
        self.song_layout.setContentsMargins(10, 10, 10, 10)
        for tr in track_info[11:16]:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            image = ClickableImage(track_id=tr["url"])
            image_url = tr["album_image"]
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.read())
            pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            rounded_pixmap = QPixmap(140, 150)
            rounded_pixmap.fill(Qt.transparent)
            painter = QPainter(rounded_pixmap)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 140, 150, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            image.setPixmap(rounded_pixmap)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]: on_image_click(turl, tname, tartist))
            main_child_layout.addWidget(image)
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            label_name = QLabel(tr["artists"])
            label_name.setObjectName("artist-name")
            label_name.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_name)
            self.song_layout.addLayout(main_child_layout)

        self.weekly_more.addLayout(self.song_layout)
        self.song_layout = QHBoxLayout()
        self.song_layout.setContentsMargins(10, 10, 10, 10)
        for tr in track_info[16:21]:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            image = ClickableImage(track_id=tr["url"])
            image_url = tr["album_image"]
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.read())
            pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            rounded_pixmap = QPixmap(140, 150)
            rounded_pixmap.fill(Qt.transparent)
            painter = QPainter(rounded_pixmap)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 140, 150, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            image.setPixmap(rounded_pixmap)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]: on_image_click(turl, tname, tartist))
            main_child_layout.addWidget(image)
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            label_name = QLabel(tr["artists"])
            label_name.setObjectName("artist-name")
            label_name.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_name)
            self.song_layout.addLayout(main_child_layout)

        self.weekly_more.addLayout(self.song_layout)

        # New releases
        below_new_label = QLabel()
        below_new_label.setText('<span>Mood</span> <span style="color: #EE10B0;">Songs</span>')
        below_new_label.setObjectName("below-label")
        home.addWidget(below_new_label)
        self.main_track_layout = QHBoxLayout()
        self.main_track_layout.setContentsMargins(10, 10, 10, 10)
        try:
            tracks = search_youtube("Sad Songs ", 20)
            track_info = []
            for track in tracks:
                track_name = track['title'][:30]
                track_artists = track["name"][:30]
                track_image_url = track["thumbnail"]
                href = track['video_id']
                url = track['video_id']
                track_info.append({
                    "name": track_name,
                    "artists": track_artists,
                    "album_image": track_image_url,
                    "href": href,
                    "url": url
                })
            for tr in track_info[2:7]:
                main_child_layout = QVBoxLayout()
                main_child_layout.setContentsMargins(0, 0, 0, 0)
                main_child_layout.setAlignment(Qt.AlignCenter)
                main_child_layout.setSpacing(10)
                image = ClickableImage(track_id=tr["url"])
                image_url = tr["album_image"]
                response = requests.get(image_url)
                response.raise_for_status()
                image_data = BytesIO(response.content)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data.read())
                pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

                rounded_pixmap = QPixmap(140, 150)
                rounded_pixmap.fill(Qt.transparent)
                painter = QPainter(rounded_pixmap)
                path = QPainterPath()
                path.addRoundedRect(0, 0, 140, 150, 10, 10)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                image.setPixmap(rounded_pixmap)
                image.setCursor(Qt.PointingHandCursor)
                image.setAlignment(Qt.AlignCenter)
                image.setObjectName("image-weekly")
                image.clicked.connect(lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]: on_image_click(turl, tname, tartist))
                main_child_layout.addWidget(image)
                label_name = QLabel(tr["name"])
                label_name.setObjectName("label-name")
                label_name.setAlignment(Qt.AlignCenter)
                label_name.setWordWrap(True)
                label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                main_child_layout.addWidget(label_name)
                label_name = QLabel(tr["artists"])
                label_name.setObjectName("artist-name")
                label_name.setAlignment(Qt.AlignCenter)
                main_child_layout.addWidget(label_name)

                self.main_track_layout.addLayout(main_child_layout)
            button_new_songs = QPushButton("Show More")
            button_new_songs.setIcon(QIcon("assets/svgs/more.svg"))
            button_new_songs.setCursor(Qt.PointingHandCursor)
            button_new_songs.setObjectName("button-view")
            button_new_songs.setIconSize(QSize(40, 40))
            self.main_track_layout.addWidget(button_new_songs)
        except Exception as e:
            not_label = QLabel("No Playlist Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.main_track_layout.addWidget(not_label)

        home.addLayout(self.main_track_layout)
        self.weekly_new = QVBoxLayout()
        self.weekly_new.setSpacing(20)
        self.weekly_new.setAlignment(Qt.AlignTop)
        self.weekly_new.setContentsMargins(2, 0, 2, 0)
        
        # New releases
        below_label = QLabel()
        below_label.setText('<span>Mood</span> <span style="color: #EE10B0;">Songs</span>')
        below_label.setObjectName("below-label")
        self.weekly_new.addWidget(below_label)

        self.song_layout = QHBoxLayout()
        self.song_layout.setContentsMargins(10, 10, 10, 10)
        for tr in track_info[0:5]:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            image = ClickableImage(track_id=tr["url"])
            image_url = tr["album_image"]
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.read())
            pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            rounded_pixmap = QPixmap(140, 150)
            rounded_pixmap.fill(Qt.transparent)
            painter = QPainter(rounded_pixmap)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 140, 150, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            image.setPixmap(rounded_pixmap)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]: on_image_click(turl, tname, tartist))
            main_child_layout.addWidget(image)
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            label_name = QLabel(tr["artists"])
            label_name.setObjectName("artist-name")
            label_name.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_name)
            self.song_layout.addLayout(main_child_layout)

        self.weekly_new.addLayout(self.song_layout)
        self.song_layout = QHBoxLayout()
        self.song_layout.setContentsMargins(10, 10, 10, 10)
        for tr in track_info[6:11]:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            image = ClickableImage(track_id=tr["url"])
            image_url = tr["album_image"]
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.read())
            pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            rounded_pixmap = QPixmap(140, 150)
            rounded_pixmap.fill(Qt.transparent)
            painter = QPainter(rounded_pixmap)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 140, 150, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            image.setPixmap(rounded_pixmap)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]: on_image_click(turl, tname, tartist))
            main_child_layout.addWidget(image)
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            label_name = QLabel(tr["artists"])
            label_name.setObjectName("artist-name")
            label_name.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_name)
            self.song_layout.addLayout(main_child_layout)

        self.weekly_new.addLayout(self.song_layout)
        self.song_layout = QHBoxLayout()
        self.song_layout.setContentsMargins(10, 10, 10, 10)
        for tr in track_info[11:16]:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            image = ClickableImage(track_id=tr["url"])
            image_url = tr["album_image"]
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.read())
            pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            rounded_pixmap = QPixmap(140, 150)
            rounded_pixmap.fill(Qt.transparent)
            painter = QPainter(rounded_pixmap)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 140, 150, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            image.setPixmap(rounded_pixmap)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]: on_image_click(turl, tname, tartist))
            main_child_layout.addWidget(image)
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            label_name = QLabel(tr["artists"])
            label_name.setObjectName("artist-name")
            label_name.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_name)
            self.song_layout.addLayout(main_child_layout)

        self.weekly_new.addLayout(self.song_layout)
        self.song_layout = QHBoxLayout()
        self.song_layout.setContentsMargins(10, 10, 10, 10)
        for tr in track_info[16:21]:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            image = ClickableImage(track_id=tr["url"])
            image_url = tr["album_image"]
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.read())
            pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            rounded_pixmap = QPixmap(140, 150)
            rounded_pixmap.fill(Qt.transparent)
            painter = QPainter(rounded_pixmap)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 140, 150, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            image.setPixmap(rounded_pixmap)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]: on_image_click(turl, tname, tartist))
            main_child_layout.addWidget(image)
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            label_name = QLabel(tr["artists"])
            label_name.setObjectName("artist-name")
            label_name.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_name)
            self.song_layout.addLayout(main_child_layout)

        self.weekly_new.addLayout(self.song_layout)

        # Weekly More widget Page
        weekly_more_widget = QWidget()
        weekly_more_widget.setLayout(self.weekly_more)
        weekly_more_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        weekly_scroll_area = QScrollArea()
        weekly_scroll_area.setWidget(weekly_more_widget)
        weekly_scroll_area.setWidgetResizable(True)
        weekly_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        weekly_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        weekly_scroll_area.setStyleSheet("QScrollArea { border: none; }")

        self.pages.addWidget(weekly_scroll_area)

        # New releases more widget page
        new_release_widget = QWidget()
        new_release_widget.setLayout(self.weekly_new)
        new_release_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        newly_scroll_area = QScrollArea()
        newly_scroll_area.setWidget(new_release_widget)
        newly_scroll_area.setWidgetResizable(True)
        newly_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        newly_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        newly_scroll_area.setStyleSheet("QScrollArea { border: none; }")        
        self.pages.addWidget(newly_scroll_area)

        # Search page
        search = QVBoxLayout()
        search.setSpacing(20)
        search.setAlignment(Qt.AlignTop)
        search.setContentsMargins(20, 20, 20, 20)  # Adjusted margins for consistency

        # Top layout for input and button
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)
        self.inputfield = QLineEdit()  # Store inputfield as instance variable
        self.inputfield.setPlaceholderText("Search Music by 🎵🎶")
        self.inputfield.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.inputfield.setMinimumHeight(40)
        self.inputfield.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
                color: black;
                min-height: 40px;
                max-height: 40px;
                width: 100%;
                margin-right: 10px;
            }
            QLineEdit:focus {
                background-color: #ffffff;
                border: 1px solid #EE10B0;
            }
        """)
        top_layout.addWidget(self.inputfield, stretch=1)

        search_button = QPushButton("Search")
        search_button.setIcon(QIcon("assets/svgs/search.svg"))
        search_button.setIconSize(QSize(20, 20))
        search_button.setObjectName("search-button")
        search_button.setCursor(Qt.PointingHandCursor)
        search_button.setFixedWidth(100)
        search_button.setMinimumHeight(40)
        search_button.setStyleSheet("""
            QPushButton#search-button {
                background-color: #EE10B0;
                color: white;
                border-radius: 8px;
                padding: 10px;
                min-height: 40px;
                max-height: 40px;
            }
            QPushButton#search-button:hover {
                background-color: #d00f9a;
            }
        """)
        top_layout.addWidget(search_button, stretch=0)

        search.addLayout(top_layout)

        # Search results layout
        self.search_layout = QVBoxLayout()
        self.search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_layout.setSpacing(20)

        # Default "No results found" label
        self.no_results_label = QLabel("Search for music  🎵🎶")
        self.no_results_label.setObjectName("no-playlist")
        self.no_results_label.setAlignment(Qt.AlignCenter)
        self.search_layout.addWidget(self.no_results_label)

        # Initialize search worker
        self.search_worker = None

        # Connect search button
        search_button.clicked.connect(self.perform_search)

        search.addLayout(self.search_layout)
        searchpage_widget = QWidget()
        searchpage_widget.setLayout(search)
        searchpage_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        searchpage_widget.setStyleSheet("QWidget { background: transparent; }")

        search_scroll_area = QScrollArea()
        search_scroll_area.setWidget(searchpage_widget)
        search_scroll_area.setWidgetResizable(True)
        search_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        search_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        search_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        self.pages.addWidget(search_scroll_area)

        # Recognize page
        recognize_layout = QVBoxLayout()
        recognize_layout.setAlignment(Qt.AlignCenter)
        recognize_layout.setSpacing(20)

        # Heading
        heading_label = GradientLabel("Song Recognizer", font_size=50)
        heading_label.setObjectName("below-label")
        heading_label.setAlignment(Qt.AlignCenter)
        recognize_layout.addWidget(heading_label)

        # Animated circle
        self.recognize_circle = AnimatedCircle()
        self.recognize_circle.setCursor(Qt.PointingHandCursor)
        self.recognize_circle.mousePressEvent = self.start_recognition
        recognize_layout.addWidget(self.recognize_circle)

        # Status label
        self.recognize_status = QLabel("Click the circle to recognize music 🎵")
        self.recognize_status.setObjectName("below-label")
        self.recognize_status.setAlignment(Qt.AlignCenter)
        recognize_layout.addWidget(self.recognize_status)

        # Results layout
        self.recognize_results = QVBoxLayout()
        self.recognize_results.setAlignment(Qt.AlignCenter)
        self.recognize_results.setSpacing(10)
        recognize_layout.addLayout(self.recognize_results)

        recognize_widget = QWidget()
        recognize_widget.setLayout(recognize_layout)
        self.recognize_page = recognize_widget

        # Other pages
        self.artist_page = QLabel("Artist 🎤")
        self.added_page = QLabel("Recently Played 🎵")
        self.played_page = QLabel("Most Played 🎵")
        self.log_page = QLabel("Logout 🎵")
        self.about_page = QLabel("About Us")

        # Set object name and alignment for QLabel pages
        for page in [self.artist_page, self.added_page, self.played_page, self.log_page, self.about_page]:
            page.setObjectName("pageLabel")
            page.setAlignment(Qt.AlignCenter)
            self.pages.addWidget(page)

        # Set object name for recognize_page (QWidget) and add to pages
        self.recognize_page.setObjectName("pageLabel")
        self.pages.addWidget(self.recognize_page)
        
        # Connect buttons to pages
        self.home_button.clicked.connect(lambda: self.activate_tab(self.home_button, home_scroll_area))
        self.search_button.clicked.connect(lambda: self.activate_tab(self.search_button, search_scroll_area))
        self.recognize.clicked.connect(lambda: self.activate_tab(self.recognize, self.recognize_page))
        self.artist.clicked.connect(lambda: self.activate_tab(self.artist, self.artist_page))
        self.added.clicked.connect(lambda: self.activate_tab(self.added, self.added_page))
        self.played.clicked.connect(lambda: self.activate_tab(self.played, self.played_page))
        self.log.clicked.connect(lambda: self.activate_tab(self.log, self.log_page))
        self.aboutbtn.clicked.connect(lambda: self.activate_tab(self.aboutbtn, self.about_page))
        button.clicked.connect(lambda: self.activate_tab(self.search_button, search_scroll_area))
        button_view.clicked.connect(lambda: self.activate_tab(self.home_button, weekly_scroll_area))
        button_new_songs.clicked.connect(lambda: self.activate_tab(self.home_button, newly_scroll_area))
        # Add to content layout
        content_layout.addWidget(sidebar_widget, 0)
        content_layout.addWidget(self.pages, 3)
        
        # Add content layout to main layout
        main_layout.addLayout(content_layout)

        # Initialize recognition worker as None
        self.recognition_worker = None

    def start_recognition(self, event):
        # Stop any existing recognition worker
        if self.recognition_worker is not None and self.recognition_worker.isRunning():
            self.recognition_worker.quit()
            self.recognition_worker.wait()
            self.recognition_worker.cleanup()
            self.recognition_worker = None

        self.recognize_circle.start_recognition()
        self.recognize_status.setText("Listening... 🎵")
        
        # Clear previous results
        while self.recognize_results.count():
            item = self.recognize_results.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Start recognition worker
        self.recognition_worker = RecognitionWorker(duration=5)
        self.recognition_worker.recognition_finished.connect(self.on_recognition_finished)
        self.recognition_worker.error_occurred.connect(self.on_recognition_error)
        self.recognition_worker.finished.connect(self.on_recognition_worker_finished)
        self.recognition_worker.start()

    def on_recognition_worker_finished(self):
        # Perform cleanup when the thread finishes
        if self.recognition_worker:
            self.recognition_worker.cleanup()
        self.recognition_worker = None

    def on_recognition_finished(self, result):
        self.recognize_circle.stop_recognition()
        
        # Check if a song was found
        if not result or 'song_title' not in result or not result['song_title']:
            self.recognize_status.setText("Song not recognized 🎵")
            not_found_label = QLabel("Song not found")
            not_found_label.setObjectName("no-playlist")
            not_found_label.setAlignment(Qt.AlignCenter)
            self.recognize_results.addWidget(not_found_label)
            return

        self.recognize_status.setText("Song recognized! 🎵")

        # Display results
        song_label = QLabel(f"🎶 Song: {result['song_title']}")
        artist_label = QLabel(f"👤 Artist: {result['artist_name']}")
        album_label = QLabel(f"💿 Album: {result['album_name']}")
        
        for label in [song_label, artist_label, album_label]:
            label.setObjectName("label-name")
            label.setAlignment(Qt.AlignCenter)
            self.recognize_results.addWidget(label)

        # Search YouTube for the song and play
        try:
            tracks = search_youtube(result['song_title'], 1)
            if tracks:
                track = tracks[0]
                track_url = track['video_id']
                track_name = track['title'][:30]
                track_artist = track['name'][:30]

                if self.playbar is not None:
                    try:
                        self.playbar.close_player()
                    except RuntimeError:
                        pass
                    self.playbar = None

                self.playbar = PlayBar(self)
                self.layout().addWidget(self.playbar)
                self.playbar.update_track_info(track_name, track_artist, "3:45")
                self.playbar.play_track(track_url)
        except Exception as e:
            error_label = QLabel("Failed to play song")
            error_label.setObjectName("no-playlist")
            error_label.setAlignment(Qt.AlignCenter)
            self.recognize_results.addWidget(error_label)

    def on_recognition_error(self, error):
        self.recognize_circle.stop_recognition()
        self.recognize_status.setText("No Song Found")
        
        error_label = QLabel("Failed to recognize song")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.recognize_results.addWidget(error_label)

    def perform_search(self):
        # Check if a previous search worker exists and is running
        if self.search_worker is not None and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait()

        search_query = self.inputfield.text().strip()
        if not search_query:
            # Clear layout and add new "No results found" label
            while self.search_layout.count():
                item = self.search_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            no_results_label = QLabel("No results found")
            no_results_label.setObjectName("no-playlist")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.search_layout.addWidget(no_results_label)
            return

        # Start new search worker
        self.search_worker = SearchWorker(search_query, 5)  # Limit to 5 results
        self.search_worker.results_fetched.connect(self.update_search_ui)
        self.search_worker.error_occurred.connect(self.show_search_error)
        self.search_worker.finished.connect(self.on_search_worker_finished)
        self.search_worker.start()

    def on_search_worker_finished(self):
        # Clear the search worker reference when it finishes
        self.search_worker = None

    def update_search_ui(self, track_info):
        # Helper function to recursively clear a layout
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                child_layout = item.layout()
                if child_layout:
                    clear_layout(child_layout)
                    child_layout.deleteLater()

        # Clear all previous content in search_layout
        clear_layout(self.search_layout)

        if not track_info:
            no_results_label = QLabel("No results found")
            no_results_label.setObjectName("no-playlist")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.search_layout.addWidget(no_results_label)
            return

        # Add header
        results_header = QLabel(f"Results for '{self.inputfield.text().strip()}'")
        results_header.setObjectName("below-label")
        self.search_layout.addWidget(results_header)

        # Create horizontal layout for tracks
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(10, 10, 10, 10)
        row_layout.setSpacing(10)

        for tr in track_info:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)

            # Create clickable image
            image = ClickableImage(track_id=tr["url"])
            try:
                response = requests.get(tr["album_image"])
                response.raise_for_status()
                image_data = BytesIO(response.content)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data.read())
                pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

                rounded_pixmap = QPixmap(140, 150)
                rounded_pixmap.fill(Qt.transparent)
                painter = QPainter(rounded_pixmap)
                path = QPainterPath()
                path.addRoundedRect(0, 0, 140, 150, 10, 10)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                image.setPixmap(rounded_pixmap)
            except:
                # Fallback to placeholder
                placeholder_pixmap = QPixmap(140, 150)
                placeholder_pixmap.fill(Qt.gray)
                image.setPixmap(placeholder_pixmap)

            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(
                lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]:
                self.on_image_click(turl, tname, tartist)
            )
            main_child_layout.addWidget(image)

            # Track name
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)

            # Artist name
            label_name = QLabel(tr["artists"])
            label_name.setObjectName("artist-name")
            label_name.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_name)

            row_layout.addLayout(main_child_layout)

        self.search_layout.addLayout(row_layout)
        self.search_layout.addStretch()

    def show_search_error(self, error):
        while self.search_layout.count():
            item = self.search_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        error_label = QLabel("Failed to fetch results")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.search_layout.addWidget(error_label)

    def on_image_click(self, track_url, track_name, artist_name):
        if self.playbar is not None:
            try:
                self.playbar.close_player()
            except RuntimeError:
                pass
            self.playbar = None

        self.playbar = PlayBar(self)
        self.layout().addWidget(self.playbar)
        self.playbar.update_track_info(track_name, artist_name, "3:45")
        self.playbar.play_track(track_url)

    def set_active_button(self, button):
        for btn in [self.home_button, self.search_button, self.recognize, self.artist, self.added, self.played, self.log, self.aboutbtn]:
            btn.setObjectName("")
            btn.setStyleSheet("")
        button.setObjectName("active-btn")
        button.setStyleSheet("")

    def activate_tab(self, button, page):
        self.set_active_button(button)
        self.pages.setCurrentWidget(page)

    def load_stylesheet(self, file_path):
        file = QFile(file_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stylesheet = QTextStream(file).readAll()
            self.setStyleSheet(stylesheet)

    def closeEvent(self, event):
        # Ensure search worker is finished before closing
        if self.search_worker is not None and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait()
        self.search_worker = None

        # Ensure recognition worker is finished before closing
        if self.recognition_worker is not None and self.recognition_worker.isRunning():
            self.recognition_worker.quit()
            self.recognition_worker.wait()
            self.recognition_worker.cleanup()
        self.recognition_worker = None

        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())