from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QScrollArea, QSizePolicy, QLineEdit, QSplashScreen
)
import sys
from PySide6.QtCore import Qt, QSize, QFile, QTextStream, QThread, Signal, QTimer, QPropertyAnimation, Property
from PySide6.QtGui import QIcon, QFontDatabase, QFont, QColor, QImage, QPixmap, QPainter, QPainterPath, QTransform, QPen
from components.gradient_label import GradientLabel
from components.playlist import search_youtube
from components.recognizer import AudioRecognizer
from io import BytesIO
from components.clickableimage import ClickableImage
from components.playbar import PlayBar
import requests
import uuid
import os
from pathlib import Path
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Example usage:
image = QImage(resource_path('assets/Banner.png'))

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
            print(f"SearchWorker: Fetching results for query '{self.query}' with max_results={self.max_results}")
            tracks = search_youtube(self.query, self.max_results)
            print(f"SearchWorker: Found {len(tracks)} tracks")
            track_info = [
                {
                    "name": track['title'][:30],
                    "artists": track["name"][:30],
                    "album_image": track["thumbnail"],
                    "url": track['video_id']
                } for track in tracks
            ]
            self.results_fetched.emit(track_info)
        except Exception as e:
            print(f"SearchWorker: Error occurred: {str(e)}")
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

# Thread for asynchronous image loading
class ImageLoader(QThread):
    image_loaded = Signal(dict, QPixmap)  # Emits the whole track dict
    error_occurred = Signal(str)

    def __init__(self, track_info):
        super().__init__()
        self.track_info = track_info

    def run(self):
        for tr in self.track_info:
            try:
                response = requests.get(tr["album_image"], timeout=5)
                response.raise_for_status()
                image_data = BytesIO(response.content)
                
                pixmap = QPixmap()
                if pixmap.loadFromData(image_data.getvalue()):  # Use getvalue() for reliable buffer access
                    pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                    rounded_pixmap = QPixmap(140, 150)
                    rounded_pixmap.fill(Qt.transparent)

                    painter = QPainter(rounded_pixmap)
                    path = QPainterPath()
                    path.addRoundedRect(0, 0, 140, 150, 10, 10)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, pixmap)
                    painter.end()

                    self.image_loaded.emit(tr, rounded_pixmap)
                else:
                    print(f"ImageLoader: Failed to load image data for {tr['album_image']}")  # Debug
                    placeholder_pixmap = QPixmap(140, 150)
                    placeholder_pixmap.fill(Qt.gray)
                    self.image_loaded.emit(tr, placeholder_pixmap)

            except Exception as e:
                print(f"ImageLoader: Error loading image {tr['album_image']}: {e}")  # Debug
                placeholder_pixmap = QPixmap(140, 150)
                placeholder_pixmap.fill(Qt.gray)
                self.image_loaded.emit(tr, placeholder_pixmap)


# Animated Circle Widget
class AnimatedCircle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self._angle = 0
        self.beat_amplitude = 0
        self.is_recognizing = False
        self.beat_timer = QTimer(self)
        self.beat_timer.timeout.connect(self.update_beat)
        self.beat_timer.start(50)
        self.rotation_animation = QPropertyAnimation(self, b"rotation_angle")
        self.rotation_animation.setDuration(10000)
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)
        self.rotation_animation.start()

    def get_rotation_angle(self):
        return self._angle

    def set_rotation_angle(self, angle):
        self._angle = angle
        self.update()

    rotation_angle = Property(float, get_rotation_angle, set_rotation_angle)

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
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 20
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(40, 40, 40))
        painter.drawEllipse(center, radius, radius)
        painter.setPen(Qt.white)
        font = QFont("Poppins", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "HiFi")
        painter.translate(center)
        painter.rotate(self._angle)
        num_bars = 60
        bar_width = 3
        max_bar_height = 20
        for i in range(num_bars):
            hue = (i * 360 / num_bars) % 360
            color = QColor.fromHsv(hue, 255, 255)
            painter.setPen(QPen(color, bar_width))
            base_height = 5
            beat_height = max_bar_height * self.beat_amplitude * (1 - abs((i % 15) - 7.5) / 7.5)
            height = base_height + beat_height
            painter.drawLine(0, radius, 0, radius + height)
            painter.rotate(360 / num_bars)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.closing = False  # Flag to prevent new threads during cleanup
        self.image_widgets = {}  # Store image widgets globally
        self.track_cache = {}  # Cache for track lists

        # Splash screen
        splash_pixmap = QPixmap()
        if os.path.exists(resource_path("assets/Logo.png")):
            splash_pixmap = QPixmap(resource_path("assets/Logo.png")).scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            splash_pixmap = QPixmap(300, 300)
            splash_pixmap.fill(Qt.gray)
        self.splash = QSplashScreen(splash_pixmap)
        self.splash.show()
        QApplication.processEvents()

        # Font setup
        font_id = QFontDatabase.addApplicationFont(resource_path("assets/fonts/Poppins-Regular.ttf"))
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.setFont(QFont(font_family, 14))
        else:
            self.setFont(QFont("Arial", 14))

        self.setWindowTitle("HiFi")
        self.setMinimumSize(1000, 1000)
        self.setWindowIcon(QIcon(resource_path("assets/Logo.png")) if os.path.exists(resource_path("assets/Logo.png")) else QIcon())
        self.load_stylesheet("style.css")

        # Main layout
        main_layout = QVBoxLayout(self)

        # Content layout
        content_layout = QHBoxLayout()

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.setSpacing(10)
        sidebar.setAlignment(Qt.AlignTop)
        sidebar.setContentsMargins(15, 15, 15, 0)

        self.head = GradientLabel("HiFi", font_size=25)
        self.head.setObjectName("label")
        sidebar.addWidget(self.head)

        self.menu = QLabel("Menu")
        self.menu.setObjectName("Menu")
        sidebar.addWidget(self.menu)

        self.home_button = QPushButton("Home")
        self.home_button.setIcon(QIcon(resource_path("assets/svgs/home.svg")) if os.path.exists(resource_path("assets/svgs/home.svg")) else QIcon())
        self.home_button.setIconSize(QSize(20, 20))
        self.home_button.setObjectName("active-btn")
        self.search_button = QPushButton("Discover")
        self.search_button.setIcon(QIcon(resource_path(resource_path("assets/svgs/search.svg"))) if os.path.exists(resource_path(resource_path("assets/svgs/search.svg"))) else QIcon())
        self.search_button.setIconSize(QSize(20, 20))
        self.recognize = QPushButton("Recognize")
        self.recognize.setIcon(QIcon(resource_path("assets/svgs/recognize.svg")) if os.path.exists(resource_path("assets/svgs/recognize.svg")) else QIcon())
        self.recognize.setIconSize(QSize(20, 20))
        self.artist = QPushButton("Artist")
        self.artist.setIcon(QIcon(resource_path("assets/svgs/Artist.svg")) if os.path.exists(resource_path("assets/svgs/Artist.svg")) else QIcon())
        self.artist.setIconSize(QSize(20, 20))
        self.played = QPushButton("Most Played")
        self.played.setIcon(QIcon(resource_path("assets/svgs/replay.svg")) if os.path.exists("assets/svgs/replay.svg") else QIcon())
        self.played.setIconSize(QSize(20, 20))
        self.my_playlists = QPushButton("My Playlists")
        self.my_playlists.setIcon(QIcon(resource_path("assets/svgs/playlist.svg")) if os.path.exists(resource_path("assets/svgs/playlist.svg")) else QIcon())
        self.my_playlists.setIconSize(QSize(20, 20))
        self.pop_genre = QPushButton("Pop")
        self.pop_genre.setIcon(QIcon(resource_path("assets/svgs/pop.svg")) if os.path.exists(resource_path("assets/svgs/pop.svg")) else QIcon())
        self.pop_genre.setIconSize(QSize(20, 20))
        self.rock_genre = QPushButton("Rock")
        self.rock_genre.setIcon(QIcon(resource_path("assets/svgs/rock.svg")) if os.path.exists(resource_path("assets/svgs/rock.svg")) else QIcon())
        self.rock_genre.setIconSize(QSize(20, 20))
        for btn in [
            self.home_button, self.search_button, self.recognize, self.artist,
            self.played, self.my_playlists, self.pop_genre, self.rock_genre
        ]:
            sidebar.addWidget(btn)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)

        about_label = QLabel("About Us")
        about_label.setObjectName("recent")
        sidebar.addWidget(about_label)
        self.aboutbtn = QPushButton("About Us")
        self.aboutbtn.setIcon(QIcon(resource_path("assets/svgs/about.svg")) if os.path.exists(resource_path("assets/svgs/about.svg")) else QIcon())
        self.aboutbtn.setIconSize(QSize(20, 20))
        self.aboutbtn.setCursor(Qt.PointingHandCursor)
        self.aboutbtn.setFixedHeight(40)
        sidebar.addWidget(self.aboutbtn)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(200)
        sidebar_widget.setObjectName("sidebar")
        content_layout.addWidget(sidebar_widget, 0)

        # Pages
        self.pages = QStackedWidget()

        # Home page
        home = QVBoxLayout()
        home.setSpacing(20)
        home.setAlignment(Qt.AlignTop)
        home.setContentsMargins(2, 0, 2, 0)

        background_label = QLabel()
        image = QImage(resource_path('assets/Banner.png')) if os.path.exists(resource_path('assets/Banner.png')) else QImage(800, 400,QImage.Format_RGB32)
        if not image.isNull():
            transform = QTransform().scale(-1, 1)
            mirrored_image = image.transformed(transform, Qt.SmoothTransformation)
            window_width = 800
            image_height = 400
            scaled_pixmap = QPixmap.fromImage(mirrored_image).scaled(
                window_width, image_height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            final_pixmap = QPixmap(window_width, image_height)
            final_pixmap.fill(Qt.transparent)
            painter = QPainter(final_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, window_width, image_height, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.fillRect(final_pixmap.rect(), QColor(0, 0, 0, 100))
            painter.end()
            background_label.setPixmap(final_pixmap)
            background_label.setScaledContents(True)
        else:
            background_label.setPixmap(QPixmap(800, 400).fill(Qt.gray))

        content_layout_background = QVBoxLayout(background_label)
        content_layout_background.setContentsMargins(20, 120, 0, 0)
        content_layout_background.setAlignment(Qt.AlignTop)
        content_layout_background.setSpacing(0)

        label1 = QLabel('<span style="font-weight: bold;">All the <span style="color: #EE10B0;">Best Songs</span> <br> in One Place</span>')
        label1.setObjectName("label1")
        content_layout_background.addWidget(label1)

        label2 = QLabel('<span>On our app, you can access an amazing collection of popular and new songs</span> <br> <span>Stream your favorite tracks in high quality and enjoy without interruptions </span> <br> <span> Whatever your taste in music, we have it all for you! </span>')
        label2.setObjectName("label2")
        content_layout_background.addWidget(label2)

        button = QPushButton("Discover Now")
        button.setCursor(Qt.PointingHandCursor)
        button.setObjectName("discover")
        button.setMaximumWidth(150)
        button.setFixedHeight(60)
        content_layout_background.addWidget(button)

        home.addWidget(background_label)

        below_label = QLabel('<span>Weekly Top</span> <span style="color: #EE10B0;">Songs</span>')
        below_label.setObjectName("below-label")
        home.addWidget(below_label)

        self.main_track_layout = QHBoxLayout()
        self.main_track_layout.setContentsMargins(10, 10, 10, 10)
        loading_label = QLabel("Loading tracks...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.main_track_layout.addWidget(loading_label)
        home.addLayout(self.main_track_layout)

        mood_label = QLabel('<span>Mood</span> <span style="color: #EE10B0;">Songs</span>')
        mood_label.setObjectName("below-label")
        home.addWidget(mood_label)

        self.mood_songs_layout = QHBoxLayout()  # Changed to QHBoxLayout
        self.mood_songs_layout.setContentsMargins(10, 10, 10, 10)
        loading_label = QLabel("Loading mood songs...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.mood_songs_layout.addWidget(loading_label)
        home.addLayout(self.mood_songs_layout)

        below_new_label = QLabel('<span>New</span> <span style="color: #EE10B0;">Releases</span>')
        below_new_label.setObjectName("below-label")
        home.addWidget(below_new_label)

        self.new_releases_layout = QHBoxLayout()
        self.new_releases_layout.setContentsMargins(10, 10, 10, 10)
        loading_label = QLabel("Loading new releases...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.new_releases_layout.addWidget(loading_label)
        home.addLayout(self.new_releases_layout)

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

        # Weekly More page
        self.weekly_more = QVBoxLayout()
        self.weekly_more.setSpacing(20)
        self.weekly_more.setAlignment(Qt.AlignTop)
        self.weekly_more.setContentsMargins(2, 0, 2, 0)
        below_label = QLabel('<span>Weekly Top</span> <span style="color: #EE10B0;">Songs</span>')
        below_label.setObjectName("below-label")
        self.weekly_more.addWidget(below_label)
        self.weekly_more_layout = QVBoxLayout()
        self.weekly_more_layout.setContentsMargins(10, 10, 10, 10)
        loading_label = QLabel("Loading weekly top songs...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.weekly_more_layout.addWidget(loading_label)
        self.weekly_more.addLayout(self.weekly_more_layout)
        weekly_more_widget = QWidget()
        weekly_more_widget.setLayout(self.weekly_more)
        weekly_more_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.weekly_scroll_area = QScrollArea()
        self.weekly_scroll_area.setWidget(weekly_more_widget)
        self.weekly_scroll_area.setWidgetResizable(True)
        self.weekly_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.weekly_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.weekly_scroll_area.setStyleSheet("QScrollArea { border: none; }")
        self.pages.addWidget(self.weekly_scroll_area)
        self.weekly_more_loaded = False

        # Mood Songs page
        self.mood_full = QVBoxLayout()
        self.mood_full.setSpacing(20)
        self.mood_full.setAlignment(Qt.AlignTop)
        self.mood_full.setContentsMargins(2, 0, 2, 0)
        below_label = QLabel('<span>Mood</span> <span style="color: #EE10B0;">Songs</span>')
        below_label.setObjectName("below-label")
        self.mood_full.addWidget(below_label)
        self.mood_full_layout = QVBoxLayout()
        self.mood_full_layout.setContentsMargins(10, 10, 10, 10)
        loading_label = QLabel("Loading mood songs...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.mood_full_layout.addWidget(loading_label)
        self.mood_full.addLayout(self.mood_full_layout)
        mood_full_widget = QWidget()
        mood_full_widget.setLayout(self.mood_full)
        mood_full_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mood_scroll_area = QScrollArea()
        self.mood_scroll_area.setWidget(mood_full_widget)
        self.mood_scroll_area.setWidgetResizable(True)
        self.mood_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.mood_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mood_scroll_area.setStyleSheet("QScrollArea { border: none; }")
        self.pages.addWidget(self.mood_scroll_area)
        self.mood_full_loaded = False

        # New Releases page
        self.weekly_new = QVBoxLayout()
        self.weekly_new.setSpacing(20)
        self.weekly_new.setAlignment(Qt.AlignTop)
        self.weekly_new.setContentsMargins(2, 0, 2, 0)
        below_label = QLabel('<span>New</span> <span style="color: #EE10B0;">Releases</span>')
        below_label.setObjectName("below-label")
        self.weekly_new.addWidget(below_label)
        self.weekly_new_layout = QVBoxLayout()
        self.weekly_new_layout.setContentsMargins(10, 10, 10, 10)
        loading_label = QLabel("Loading new releases...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.weekly_new_layout.addWidget(loading_label)
        self.weekly_new.addLayout(self.weekly_new_layout)
        new_release_widget = QWidget()
        new_release_widget.setLayout(self.weekly_new)
        new_release_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.newly_scroll_area = QScrollArea()
        self.newly_scroll_area.setWidget(new_release_widget)
        self.newly_scroll_area.setWidgetResizable(True)
        self.newly_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.newly_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.newly_scroll_area.setStyleSheet("QScrollArea { border: none; }")
        self.pages.addWidget(self.newly_scroll_area)
        self.weekly_new_loaded = False

        # Search page
        search = QVBoxLayout()
        search.setSpacing(20)
        search.setAlignment(Qt.AlignTop)
        search.setContentsMargins(20, 20, 20, 20)
        top_layout = QHBoxLayout()
        self.inputfield = QLineEdit()
        self.inputfield.setPlaceholderText("Search Music by 🎵🎶")
        self.inputfield.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.inputfield.setMinimumHeight(40)
        self.inputfield.setStyleSheet("""
            QLineEdit { background-color: white; border-radius: 8px; padding: 10px; font-size: 15px; color: black; min-height: 40px; max-height: 40px; }
            QLineEdit:focus { border: 1px solid #EE10B0; }
        """)
        top_layout.addWidget(self.inputfield, stretch=1)
        search_button = QPushButton("Search")
        search_button.setIcon(QIcon(resource_path("assets/svgs/search.svg")) if os.path.exists(resource_path("assets/svgs/search.svg")) else QIcon())
        search_button.setIconSize(QSize(20, 20))
        search_button.setObjectName("search-button")
        search_button.setCursor(Qt.PointingHandCursor)
        search_button.setFixedWidth(100)
        search_button.setMinimumHeight(40)
        top_layout.addWidget(search_button, stretch=0)
        search.addLayout(top_layout)
        self.search_layout = QVBoxLayout()
        self.search_layout.setContentsMargins(0, 0, 0, 0)
        self.no_results_label = QLabel("Search for music  🎵🎶")
        self.no_results_label.setObjectName("no-playlist")
        self.no_results_label.setAlignment(Qt.AlignCenter)
        self.search_layout.addWidget(self.no_results_label)
        search.addLayout(self.search_layout)
        searchpage_widget = QWidget()
        searchpage_widget.setLayout(search)
        searchpage_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        search_scroll_area = QScrollArea()
        search_scroll_area.setWidget(searchpage_widget)
        search_scroll_area.setWidgetResizable(True)
        search_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        search_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        search_scroll_area.setStyleSheet("QScrollArea { border: none; }")
        self.pages.addWidget(search_scroll_area)
        search_button.clicked.connect(self.perform_search)

        # Recognize page
        recognize_layout = QVBoxLayout()
        recognize_layout.setAlignment(Qt.AlignCenter)
        recognize_layout.setSpacing(20)
        self.recognize_circle = AnimatedCircle()
        self.recognize_circle.setCursor(Qt.PointingHandCursor)
        self.recognize_circle.mousePressEvent = self.start_recognition
        recognize_layout.addWidget(self.recognize_circle)
        self.recognize_status = QLabel("Click the circle to recognize music 🎵")
        self.recognize_status.setObjectName("below-label")
        self.recognize_status.setAlignment(Qt.AlignCenter)
        recognize_layout.addWidget(self.recognize_status)
        self.recognize_results = QVBoxLayout()
        self.recognize_results.setAlignment(Qt.AlignCenter)
        recognize_layout.addLayout(self.recognize_results)
        self.recognize_page = QWidget()
        self.recognize_page.setLayout(recognize_layout)
        self.recognize_page.setObjectName("pageLabel")
        self.pages.addWidget(self.recognize_page)

        # Artist page
        artist_layout = QVBoxLayout()
        artist_layout.setSpacing(20)
        artist_layout.setAlignment(Qt.AlignTop)
        artist_layout.setContentsMargins(20, 20, 20, 20)
        artist_top_layout = QHBoxLayout()
        self.artist_inputfield = QLineEdit()
        self.artist_inputfield.setPlaceholderText("Search Artist by 🎤")
        self.artist_inputfield.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.artist_inputfield.setMinimumHeight(40)
        self.artist_inputfield.setStyleSheet("""
            QLineEdit { background-color: white; border-radius: 8px; padding: 10px; font-size: 15px; color: black; min-height: 40px; max-height: 40px; }
            QLineEdit:focus { border: 1px solid #EE10B0; }
        """)
        artist_top_layout.addWidget(self.artist_inputfield, stretch=1)
        artist_search_button = QPushButton("Search")
        artist_search_button.setIcon(QIcon(resource_path("assets/svgs/search.svg")) if os.path.exists(resource_path("assets/svgs/search.svg")) else QIcon())
        artist_search_button.setIconSize(QSize(20, 20))
        artist_search_button.setObjectName("search-button")
        artist_search_button.setCursor(Qt.PointingHandCursor)
        artist_search_button.setFixedWidth(100)
        artist_search_button.setMinimumHeight(40)
        artist_top_layout.addWidget(artist_search_button, stretch=0)
        artist_layout.addLayout(artist_top_layout)
        self.artist_layout = QVBoxLayout()
        self.artist_layout.setContentsMargins(0, 0, 0, 0)
        self.artist_no_results_label = QLabel("Search for artists  🎤")
        self.artist_no_results_label.setObjectName("no-playlist")
        self.artist_no_results_label.setAlignment(Qt.AlignCenter)
        self.artist_layout.addWidget(self.artist_no_results_label)
        artist_layout.addLayout(self.artist_layout)
        artistpage_widget = QWidget()
        artistpage_widget.setLayout(artist_layout)
        artistpage_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.artist_page = QScrollArea()
        self.artist_page.setWidget(artistpage_widget)
        self.artist_page.setWidgetResizable(True)
        self.artist_page.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.artist_page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.artist_page.setStyleSheet("QScrollArea { border: none; }")
        self.pages.addWidget(self.artist_page)
        artist_search_button.clicked.connect(self.perform_artist_search)

        # Most Played page
        most_played_layout = QVBoxLayout()
        most_played_layout.setSpacing(20)
        most_played_layout.setAlignment(Qt.AlignTop)
        most_played_layout.setContentsMargins(20, 20, 20, 20)
        most_played_header = QLabel("Most Played Songs 🎵")
        most_played_header.setObjectName("below-label")
        most_played_layout.addWidget(most_played_header)
        self.most_played_layout = QVBoxLayout()
        self.most_played_layout.setContentsMargins(0, 0, 0, 0)
        loading_label = QLabel("Loading most played songs...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.most_played_layout.addWidget(loading_label)
        most_played_layout.addLayout(self.most_played_layout)
        most_played_widget = QWidget()
        most_played_widget.setLayout(most_played_layout)
        self.played_page = QScrollArea()
        self.played_page.setWidget(most_played_widget)
        self.played_page.setWidgetResizable(True)
        self.played_page.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.played_page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.played_page.setStyleSheet("QScrollArea { border: none; }")
        self.pages.addWidget(self.played_page)
        self.most_played_loaded = False

        # My Playlists page
        playlists_layout = QVBoxLayout()
        playlists_layout.setSpacing(20)
        playlists_layout.setAlignment(Qt.AlignTop)
        playlists_layout.setContentsMargins(20, 20, 20, 20)
        playlists_header = QLabel("My Playlists 🎶")
        playlists_header.setObjectName("below-label")
        playlists_layout.addWidget(playlists_header)
        self.playlists_layout = QVBoxLayout()
        self.playlists_layout.setContentsMargins(0, 0, 0, 0)
        loading_label = QLabel("Loading playlists...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.playlists_layout.addWidget(loading_label)
        playlists_layout.addLayout(self.playlists_layout)
        playlists_widget = QWidget()
        playlists_widget.setLayout(playlists_layout)
        self.my_playlists_page = QScrollArea()
        self.my_playlists_page.setWidget(playlists_widget)
        self.my_playlists_page.setWidgetResizable(True)
        self.my_playlists_page.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.my_playlists_page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.my_playlists_page.setStyleSheet("QScrollArea { border: none; }")
        self.pages.addWidget(self.my_playlists_page)
        self.playlists_loaded = False

        # Pop Genre page
        pop_layout = QVBoxLayout()
        pop_layout.setSpacing(20)
        pop_layout.setAlignment(Qt.AlignTop)
        pop_layout.setContentsMargins(20, 20, 20, 20)
        pop_header = QLabel("Pop Music 🎶")
        pop_header.setObjectName("below-label")
        pop_layout.addWidget(pop_header)
        self.pop_layout = QVBoxLayout()
        self.pop_layout.setContentsMargins(0, 0, 0, 0)
        loading_label = QLabel("Loading pop songs...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.pop_layout.addWidget(loading_label)
        pop_layout.addLayout(self.pop_layout)
        pop_widget = QWidget()
        pop_widget.setLayout(pop_layout)
        self.pop_genre_page = QScrollArea()
        self.pop_genre_page.setWidget(pop_widget)
        self.pop_genre_page.setWidgetResizable(True)
        self.pop_genre_page.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pop_genre_page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pop_genre_page.setStyleSheet("QScrollArea { border: none; }")
        self.pages.addWidget(self.pop_genre_page)
        self.pop_loaded = False

        # Rock Genre page
        rock_layout = QVBoxLayout()
        rock_layout.setSpacing(20)
        rock_layout.setAlignment(Qt.AlignTop)
        rock_layout.setContentsMargins(20, 20, 20, 20)
        rock_header = QLabel("Rock Music 🎶")
        rock_header.setObjectName("below-label")
        rock_layout.addWidget(rock_header)
        self.rock_layout = QVBoxLayout()
        self.rock_layout.setContentsMargins(0, 0, 0, 0)
        loading_label = QLabel("Loading rock songs...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.rock_layout.addWidget(loading_label)
        rock_layout.addLayout(self.rock_layout)
        rock_widget = QWidget()
        rock_widget.setLayout(rock_layout)
        self.rock_genre_page = QScrollArea()
        self.rock_genre_page.setWidget(rock_widget)
        self.rock_genre_page.setWidgetResizable(True)
        self.rock_genre_page.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rock_genre_page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.rock_genre_page.setStyleSheet("QScrollArea { border: none; }")
        self.pages.addWidget(self.rock_genre_page)
        self.rock_loaded = False

        # About Us page
        about_layout = QVBoxLayout()
        about_layout.setSpacing(20)
        about_layout.setAlignment(Qt.AlignTop)
        about_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        about_header = QLabel("About Us")
        about_header.setObjectName("below-label")
        about_layout.addWidget(about_header)

        # Description
        about_description = QLabel("We are a passionate team dedicated to bringing you the best music streaming experience.")
        about_description.setObjectName("label-name")
        about_description.setAlignment(Qt.AlignCenter)
        about_description.setWordWrap(True)
        about_layout.addWidget(about_description)

        # Team Members
        team_layout = QHBoxLayout()
        team_layout.setSpacing(20)
        team_members = [
    ("Moeez Sheikh", "Developer", "assets/Moeez.png"),
]
        for name, role, image_path in team_members:
            member_layout = QVBoxLayout()
            avatar = QLabel()
            pixmap = QPixmap()
            if os.path.exists(resource_path(image_path)):
                pixmap.load(resource_path(image_path))  # Use resource_path for PyInstaller
                pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                print(f"About Us: Image {image_path} not found, using placeholder")  # Debug
                pixmap = QPixmap(100, 100)
                pixmap.fill(Qt.gray)
            
            rounded_pixmap = QPixmap(120, 120)
            rounded_pixmap.fill(Qt.transparent)
            painter = QPainter(rounded_pixmap)
            path = QPainterPath()
            path.addEllipse(0, 0, 100, 100)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            avatar.setPixmap(rounded_pixmap)
            avatar.setAlignment(Qt.AlignCenter)
            member_layout.addWidget(avatar)
            name_label = QLabel(name)
            name_label.setObjectName("label-name")
            name_label.setAlignment(Qt.AlignCenter)
            member_layout.addWidget(name_label)
            role_label = QLabel(role)
            role_label.setObjectName("artist-name")
            role_label.setAlignment(Qt.AlignCenter)
            member_layout.addWidget(role_label)
            team_layout.addLayout(member_layout)

        about_layout.addLayout(team_layout)

        contact_layout = QVBoxLayout()
        contact_layout.setSpacing(10)
        contact_layout.setAlignment(Qt.AlignCenter)

        contact_header = QLabel("Contact Us")
        contact_header.setObjectName("below-label")
        contact_header.setAlignment(Qt.AlignCenter)
        contact_layout.addWidget(contact_header)

        contact_email = QLabel("📧 Email: support@hifi.com")
        contact_email.setObjectName("label-name")
        contact_email.setAlignment(Qt.AlignCenter)
        contact_layout.addWidget(contact_email)

        about_layout.addLayout(contact_layout)
        about_widget = QWidget()
        about_widget.setLayout(about_layout)

        self.about_page = QScrollArea()
        self.about_page.setWidget(about_widget)
        self.about_page.setWidgetResizable(True)
        self.about_page.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.about_page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.about_page.setStyleSheet("QScrollArea { border: none; }")

        self.pages.addWidget(self.about_page)

        # Connect buttons
        self.home_button.clicked.connect(lambda: self.activate_tab(self.home_button, home_scroll_area, self.perform_home_search))
        self.search_button.clicked.connect(lambda: self.activate_tab(self.search_button, search_scroll_area))
        self.recognize.clicked.connect(lambda: self.activate_tab(self.recognize, self.recognize_page))
        self.artist.clicked.connect(lambda: self.activate_tab(self.artist, self.artist_page))
        self.played.clicked.connect(lambda: self.activate_tab(self.played, self.played_page, self.perform_most_played_search))
        self.my_playlists.clicked.connect(lambda: self.activate_tab(self.my_playlists, self.my_playlists_page, self.perform_playlists_search))
        self.pop_genre.clicked.connect(lambda: self.activate_tab(self.pop_genre, self.pop_genre_page, self.perform_pop_search))
        self.rock_genre.clicked.connect(lambda: self.activate_tab(self.rock_genre, self.rock_genre_page, self.perform_rock_search))
        self.aboutbtn.clicked.connect(lambda: self.activate_tab(self.aboutbtn, self.about_page))
        button.clicked.connect(lambda: self.activate_tab(self.search_button, search_scroll_area))

        content_layout.addWidget(self.pages, 3)
        main_layout.addLayout(content_layout)

        self.playbar = None
        self.search_worker = None
        self.artist_search_worker = None
        self.recognition_worker = None
        self.image_loaders = []  # List to track all ImageLoader threads

        # Initialize content after UI is rendered
        QTimer.singleShot(200, self.initialize_content)

    def initialize_content(self):
        if not self.closing:
            self.perform_home_search()
        self.splash.close()

    def perform_home_search(self):
        if self.closing or (hasattr(self, 'home_loaded') and self.home_loaded):
            return
        self.search_worker = SearchWorker("Coke Studio", 25)  # Fetch 25 for cache
        self.search_worker.results_fetched.connect(self.update_home_ui)
        self.search_worker.error_occurred.connect(self.show_home_search_error)
        self.search_worker.finished.connect(self.on_search_worker_finished)
        self.search_worker.start()
        self.home_loaded = True

    def perform_weekly_more_search(self):
        if self.closing or self.weekly_more_loaded:
            return
        if "weekly_top" in self.track_cache:
            self.update_weekly_more_ui(self.track_cache["weekly_top"])
        else:
            self.search_worker = SearchWorker("Weekly Top Songs", 25)
            self.search_worker.results_fetched.connect(self.update_weekly_more_ui)
            self.search_worker.error_occurred.connect(self.show_weekly_more_search_error)
            self.search_worker.finished.connect(self.on_search_worker_finished)
            self.search_worker.start()
        self.weekly_more_loaded = True

    def perform_mood_songs_search(self):
        if self.closing or (hasattr(self, 'mood_loaded') and self.mood_loaded):
            return
        self.search_worker = SearchWorker("Mood Songs", 20)
        self.search_worker.results_fetched.connect(self.update_mood_songs_ui)
        self.search_worker.error_occurred.connect(self.show_mood_songs_search_error)
        self.search_worker.finished.connect(self.on_search_worker_finished)
        self.search_worker.start()
        self.mood_loaded = True

    def perform_mood_full_search(self):
        if self.closing or self.mood_full_loaded:
            return
        if "mood_songs" in self.track_cache:
            self.update_mood_full_ui(self.track_cache["mood_songs"])
        else:
            self.search_worker = SearchWorker("Mood Songs", 20)
            self.search_worker.results_fetched.connect(self.update_mood_full_ui)
            self.search_worker.error_occurred.connect(self.show_mood_full_search_error)
            self.search_worker.finished.connect(self.on_search_worker_finished)
            self.search_worker.start()
        self.mood_full_loaded = True

    def perform_new_releases_search(self):
        if self.closing or self.weekly_new_loaded:
            return
        self.search_worker = SearchWorker("New music releases", 25)
        self.search_worker.results_fetched.connect(self.update_new_releases_ui)
        self.search_worker.error_occurred.connect(self.show_new_releases_search_error)
        self.search_worker.finished.connect(self.on_search_worker_finished)
        self.search_worker.start()
        self.weekly_new_loaded = True

    def perform_new_releases_full_search(self):
        if self.closing or self.weekly_new_loaded:
            return
        if "new_releases" in self.track_cache:
            self.update_new_releases_full_ui(self.track_cache["new_releases"])
        else:
            self.search_worker = SearchWorker("New music releases", 25)
            self.search_worker.results_fetched.connect(self.update_new_releases_full_ui)
            self.search_worker.error_occurred.connect(self.show_new_releases_search_error)
            self.search_worker.finished.connect(self.on_search_worker_finished)
            self.search_worker.start()

    def perform_playlists_search(self):
        if self.closing or self.playlists_loaded:
            return
        self.search_worker = SearchWorker("Top Playlists", 25)
        self.search_worker.results_fetched.connect(self.update_playlists_ui)
        self.search_worker.error_occurred.connect(self.show_playlists_search_error)
        self.search_worker.finished.connect(self.on_search_worker_finished)
        self.search_worker.start()
        self.playlists_loaded = True

    def perform_pop_search(self):
        if self.closing or self.pop_loaded:
            return
        self.search_worker = SearchWorker("Pop music", 25)
        self.search_worker.results_fetched.connect(self.update_pop_ui)
        self.search_worker.error_occurred.connect(self.show_pop_search_error)
        self.search_worker.finished.connect(self.on_search_worker_finished)
        self.search_worker.start()
        self.pop_loaded = True

    def perform_rock_search(self):
        if self.closing or self.rock_loaded:
            return
        self.search_worker = SearchWorker("Rock music", 25)
        self.search_worker.results_fetched.connect(self.update_rock_ui)
        self.search_worker.error_occurred.connect(self.show_rock_search_error)
        self.search_worker.finished.connect(self.on_search_worker_finished)
        self.search_worker.start()
        self.rock_loaded = True

    def perform_most_played_search(self):
        if self.closing or self.most_played_loaded:
            return
        self.search_worker = SearchWorker("Popular song of all time", 25)
        self.search_worker.results_fetched.connect(self.update_most_played_ui)
        self.search_worker.error_occurred.connect(self.show_most_played_search_error)
        self.search_worker.finished.connect(self.on_search_worker_finished)
        self.search_worker.start()
        self.most_played_loaded = True

    def perform_search(self):
        if self.closing:
            return
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait()
        search_query = self.inputfield.text().strip()
        if not search_query:
            self.clear_layout(self.search_layout)
            no_results_label = QLabel("Please enter a search query")
            no_results_label.setObjectName("no-playlist")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.search_layout.addWidget(no_results_label)
            return
        print(f"Performing search for: {search_query}")
        self.clear_layout(self.search_layout)  # Clear layout before starting search
        loading_label = QLabel("Searching...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.search_layout.addWidget(loading_label)
        self.search_worker = SearchWorker(search_query, 5)
        self.search_worker.results_fetched.connect(self.update_search_ui)
        self.search_worker.error_occurred.connect(self.show_search_error)
        self.search_worker.finished.connect(self.on_search_worker_finished)
        self.search_worker.start()

    def perform_artist_search(self):
        if self.closing:
            return
        if self.artist_search_worker and self.artist_search_worker.isRunning():
            self.artist_search_worker.quit()
            self.artist_search_worker.wait()
        search_query = self.artist_inputfield.text().strip()
        if not search_query:
            self.clear_layout(self.artist_layout)
            no_results_label = QLabel("Please enter an artist name")
            no_results_label.setObjectName("no-playlist")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.artist_layout.addWidget(no_results_label)
            return
        print(f"Performing artist search for: {search_query}")
        self.clear_layout(self.artist_layout)  # Clear layout before starting search
        loading_label = QLabel("Searching...")
        loading_label.setObjectName("no-playlist")
        loading_label.setAlignment(Qt.AlignCenter)
        self.artist_layout.addWidget(loading_label)
        self.artist_search_worker = SearchWorker(f"{search_query} popular songs", 4)
        self.artist_search_worker.results_fetched.connect(self.update_artist_ui)
        self.artist_search_worker.error_occurred.connect(self.show_artist_search_error)
        self.artist_search_worker.finished.connect(self.on_artist_search_worker_finished)
        self.artist_search_worker.start()

    def start_recognition(self, event):
        if self.closing:
            return
        if self.recognition_worker and self.recognition_worker.isRunning():
            self.recognition_worker.quit()
            self.recognition_worker.wait()
            self.recognition_worker.cleanup()
        self.recognize_circle.start_recognition()
        self.recognize_status.setText("Listening... 🎵")
        self.clear_layout(self.recognize_results)
        self.recognition_worker = RecognitionWorker(duration=8)
        self.recognition_worker.recognition_finished.connect(self.on_recognition_finished)
        self.recognition_worker.error_occurred.connect(self.on_recognition_error)
        self.recognition_worker.finished.connect(self.on_recognition_worker_finished)
        self.recognition_worker.start()

    def on_recognition_finished(self, result):
        self.recognize_circle.stop_recognition()
        if not result or 'song_title' not in result or not result['song_title']:
            self.recognize_status.setText("Song not recognized 🎵")
            not_found_label = QLabel("Song not found")
            not_found_label.setObjectName("no-playlist")
            not_found_label.setAlignment(Qt.AlignCenter)
            self.recognize_results.addWidget(not_found_label)
            return
        self.recognize_status.setText("Song recognized! 🎵")
        song_label = QLabel(f"🎶 Song: {result['song_title']}")
        artist_label = QLabel(f"👤 Artist: {result['artist_name']}")
        for label in [song_label, artist_label]:
            label.setObjectName("label-name")
            label.setAlignment(Qt.AlignCenter)
            self.recognize_results.addWidget(label)
        try:
            tracks = search_youtube(result['song_title'], 1)
            if tracks:
                track = tracks[0]
                self.on_image_click(track['video_id'], track['title'][:30], track['name'][:30])
        except Exception:
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

    def on_recognition_worker_finished(self):
        if self.recognition_worker:
            self.recognition_worker.cleanup()
            self.recognition_worker = None

    def on_search_worker_finished(self):
        self.search_worker = None

    def on_artist_search_worker_finished(self):
        self.artist_search_worker = None

    def on_image_loader_finished(self, loader):
        if loader in self.image_loaders:
            self.image_loaders.remove(loader)

    def update_home_ui(self, track_info):
        self.track_cache["weekly_top"] = track_info
        self.clear_layout(self.main_track_layout)
        if not track_info:
            not_label = QLabel("No Playlist Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.main_track_layout.addWidget(not_label)
            return
        
        # Show only first 5 tracks initially
        initial_tracks = track_info[:5]
        
        # Create layout for the initial 5 tracks
        tracks_layout = QHBoxLayout()
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        tracks_layout.setSpacing(20)
        
        for tr in initial_tracks:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            
            # Create the image widget with placeholder
            image = ClickableImage(track_id=tr["url"])
            placeholder = QPixmap(140, 150)
            placeholder.fill(Qt.gray)
            image.setPixmap(placeholder)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(
                lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]:
                self.on_image_click(turl, tname, tartist)
            )
            self.image_widgets[tr["url"]] = image
            main_child_layout.addWidget(image)
            
            # Add track name
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            
            # Add artist name
            label_artist = QLabel(tr["artists"])
            label_artist.setObjectName("artist-name")
            label_artist.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_artist)
            
            tracks_layout.addLayout(main_child_layout)
        
        # Add the tracks layout to main layout
        self.main_track_layout.addLayout(tracks_layout)
        
        # Add "Show More" button if there are more tracks
        if len(track_info) > 5:
            button_view = QPushButton("Show More")
            button_view.setIcon(QIcon(resource_path("assets/svgs/more.svg")) if os.path.exists(resource_path("assets/svgs/more.svg")) else QIcon())
            button_view.setCursor(Qt.PointingHandCursor)
            button_view.setObjectName("button-view")
            button_view.setIconSize(QSize(40, 40))
            self.main_track_layout.addWidget(button_view, alignment=Qt.AlignCenter)
            button_view.clicked.connect(lambda: self.activate_tab(self.home_button, self.weekly_scroll_area, self.perform_weekly_more_search))
        
        # Load images asynchronously
        image_loader = ImageLoader(initial_tracks)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(
            lambda track, pixmap: self.update_track_image(self.main_track_layout, track, pixmap, initial_tracks)
        )
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()
        
        QTimer.singleShot(100, self.perform_mood_songs_search)

    def update_weekly_more_ui(self, track_info):
        self.clear_layout(self.weekly_more_layout)
        if not track_info:
            not_label = QLabel("No Weekly Top Songs Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.weekly_more_layout.addWidget(not_label)
            return
        image_loader = ImageLoader(track_info)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.weekly_more_layout, track, pixmap, track_info, rows=True))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()

    def update_mood_songs_ui(self, track_info):
        self.track_cache["mood_songs"] = track_info
        self.clear_layout(self.mood_songs_layout)
        if not track_info:
            not_label = QLabel("No Mood Songs Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.mood_songs_layout.addWidget(not_label)
            return
        
        # Show only first 5 tracks initially
        initial_tracks = track_info[:5]
        
        # Create layout for the initial 5 tracks
        tracks_layout = QHBoxLayout()
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        tracks_layout.setSpacing(20)
        
        for tr in initial_tracks:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            
            # Create the image widget with placeholder
            image = ClickableImage(track_id=tr["url"])
            placeholder = QPixmap(140, 150)
            placeholder.fill(Qt.gray)
            image.setPixmap(placeholder)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(
                lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]:
                self.on_image_click(turl, tname, tartist)
            )
            self.image_widgets[tr["url"]] = image
            main_child_layout.addWidget(image)
            
            # Add track name
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            
            # Add artist name
            label_artist = QLabel(tr["artists"])
            label_artist.setObjectName("artist-name")
            label_artist.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_artist)
            
            tracks_layout.addLayout(main_child_layout)
        
        # Add the tracks layout to mood songs layout
        self.mood_songs_layout.addLayout(tracks_layout)
        
        # Add "Show More" button
        button_view = QPushButton("Show More")
        button_view.setIcon(QIcon(resource_path("assets/svgs/more.svg")) if os.path.exists(resource_path("assets/svgs/more.svg")) else QIcon())
        button_view.setCursor(Qt.PointingHandCursor)
        button_view.setObjectName("button-view")
        button_view.setIconSize(QSize(40, 40))
        self.mood_songs_layout.addWidget(button_view, alignment=Qt.AlignCenter)
        button_view.clicked.connect(lambda: self.activate_tab(self.home_button, self.mood_scroll_area, self.perform_mood_full_search))
        
        # Load images asynchronously
        image_loader = ImageLoader(initial_tracks)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.mood_songs_layout, track, pixmap, initial_tracks))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()
        
        QTimer.singleShot(100, self.perform_new_releases_search)

    def update_mood_full_ui(self, track_info):
        self.clear_layout(self.mood_full_layout)
        if not track_info:
            not_label = QLabel("No Mood Songs Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.mood_full_layout.addWidget(not_label)
            return
        image_loader = ImageLoader(track_info)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.mood_full_layout, track, pixmap, track_info, rows=True))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()

    def update_new_releases_ui(self, track_info):
        self.track_cache["new_releases"] = track_info
        self.clear_layout(self.new_releases_layout)
        if not track_info:
            not_label = QLabel("No New Releases Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.new_releases_layout.addWidget(not_label)
            return
        
        # Show only first 5 tracks initially
        initial_tracks = track_info[:5]
        
        # Create layout for the initial 5 tracks
        tracks_layout = QHBoxLayout()
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        tracks_layout.setSpacing(20)
        
        for tr in initial_tracks:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            
            # Create the image widget with placeholder
            image = ClickableImage(track_id=tr["url"])
            placeholder = QPixmap(140, 150)
            placeholder.fill(Qt.gray)
            image.setPixmap(placeholder)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(
                lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]:
                self.on_image_click(turl, tname, tartist)
            )
            self.image_widgets[tr["url"]] = image
            main_child_layout.addWidget(image)
            
            # Add track name
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            
            # Add artist name
            label_artist = QLabel(tr["artists"])
            label_artist.setObjectName("artist-name")
            label_artist.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_artist)
            
            tracks_layout.addLayout(main_child_layout)
        
        # Add the tracks layout to new releases layout
        self.new_releases_layout.addLayout(tracks_layout)
        
        # Add "Show More" button
        button_new_songs = QPushButton("Show More")
        button_new_songs.setIcon(QIcon(resource_path("assets/svgs/more.svg")) if os.path.exists(resource_path("assets/svgs/more.svg")) else QIcon())
        button_new_songs.setCursor(Qt.PointingHandCursor)
        button_new_songs.setObjectName("button-view")
        button_new_songs.setIconSize(QSize(40, 40))
        self.new_releases_layout.addWidget(button_new_songs, alignment=Qt.AlignCenter)
        button_new_songs.clicked.connect(lambda: self.activate_tab(self.home_button, self.newly_scroll_area, self.perform_new_releases_full_search))
        
        # Load images asynchronously
        image_loader = ImageLoader(initial_tracks)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.new_releases_layout, track, pixmap, initial_tracks))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()

    def update_new_releases_full_ui(self, track_info):
        self.clear_layout(self.weekly_new_layout)
        if not track_info:
            not_label = QLabel("No New Releases Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.weekly_new_layout.addWidget(not_label)
            return
        image_loader = ImageLoader(track_info)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.weekly_new_layout, track, pixmap, track_info, rows=True))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()

    def update_playlists_ui(self, track_info):
        self.clear_layout(self.playlists_layout)
        if not track_info:
            not_label = QLabel("No Playlists Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.playlists_layout.addWidget(not_label)
            return
        image_loader = ImageLoader(track_info)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.playlists_layout, track, pixmap, track_info, rows=True))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()

    def update_pop_ui(self, track_info):
        self.clear_layout(self.pop_layout)
        if not track_info:
            not_label = QLabel("No Pop Songs Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.pop_layout.addWidget(not_label)
            return
        image_loader = ImageLoader(track_info)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.pop_layout, track, pixmap, track_info, rows=True))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()

    def update_rock_ui(self, track_info):
        self.clear_layout(self.rock_layout)
        if not track_info:
            not_label = QLabel("No Rock Songs Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            self.rock_layout.addWidget(not_label)
            return
        image_loader = ImageLoader(track_info)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.rock_layout, track, pixmap, track_info, rows=True))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()

    def update_search_ui(self, track_info):
        self.clear_layout(self.search_layout)
        if not track_info:
            no_results_label = QLabel(f"No results found for '{self.inputfield.text().strip()}'")
            no_results_label.setObjectName("no-playlist")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.search_layout.addWidget(no_results_label)
            return
        
        # Add results header
        results_header = QLabel(f"Results for '{self.inputfield.text().strip()}'")
        results_header.setObjectName("below-label")
        self.search_layout.addWidget(results_header)
        
        # Create horizontal layout for tracks
        tracks_layout = QHBoxLayout()
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        tracks_layout.setSpacing(20)
        
        for tr in track_info:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            
            # Create the image widget with placeholder
            image = ClickableImage(track_id=tr["url"])
            placeholder = QPixmap(140, 150)
            placeholder.fill(Qt.gray)
            image.setPixmap(placeholder)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(
                lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]:
                self.on_image_click(turl, tname, tartist)
            )
            self.image_widgets[tr["url"]] = image
            main_child_layout.addWidget(image)
            
            # Add track name
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            
            # Add artist name
            label_artist = QLabel(tr["artists"])
            label_artist.setObjectName("artist-name")
            label_artist.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_artist)
            
            tracks_layout.addLayout(main_child_layout)
        
        # Add tracks layout to search layout
        self.search_layout.addLayout(tracks_layout)
        self.search_layout.addStretch()  # Push content to top
        
        # Load images asynchronously
        image_loader = ImageLoader(track_info)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.search_layout, track, pixmap, track_info))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()

    def update_artist_ui(self, track_info):
        self.clear_layout(self.artist_layout)
        if not track_info:
            no_results_label = QLabel(f"No results found for '{self.artist_inputfield.text().strip()}'")
            no_results_label.setObjectName("no-playlist")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.artist_layout.addWidget(no_results_label)
            return
        
        # Add results header
        results_header = QLabel(f"Popular songs for '{self.artist_inputfield.text().strip()}'")
        results_header.setObjectName("below-label")
        self.artist_layout.addWidget(results_header)
        
        # Create horizontal layout for tracks
        tracks_layout = QHBoxLayout()
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        tracks_layout.setSpacing(20)
        
        for tr in track_info:
            main_child_layout = QVBoxLayout()
            main_child_layout.setContentsMargins(0, 0, 0, 0)
            main_child_layout.setAlignment(Qt.AlignCenter)
            main_child_layout.setSpacing(10)
            
            # Create the image widget with placeholder
            image = ClickableImage(track_id=tr["url"])
            placeholder = QPixmap(140, 150)
            placeholder.fill(Qt.gray)
            image.setPixmap(placeholder)
            image.setCursor(Qt.PointingHandCursor)
            image.setAlignment(Qt.AlignCenter)
            image.setObjectName("image-weekly")
            image.clicked.connect(
                lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]:
                self.on_image_click(turl, tname, tartist)
            )
            self.image_widgets[tr["url"]] = image
            main_child_layout.addWidget(image)
            
            # Add track name
            label_name = QLabel(tr["name"])
            label_name.setObjectName("label-name")
            label_name.setAlignment(Qt.AlignCenter)
            label_name.setWordWrap(True)
            label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_child_layout.addWidget(label_name)
            
            # Add artist name
            label_artist = QLabel(tr["artists"])
            label_artist.setObjectName("artist-name")
            label_artist.setAlignment(Qt.AlignCenter)
            main_child_layout.addWidget(label_artist)
            
            tracks_layout.addLayout(main_child_layout)
        
        # Add tracks layout to artist layout
        self.artist_layout.addLayout(tracks_layout)
        self.artist_layout.addStretch()  # Push content to top
        
        # Load images asynchronously
        image_loader = ImageLoader(track_info)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.artist_layout, track, pixmap, track_info))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()

    def update_most_played_ui(self, track_info):
        self.clear_layout(self.most_played_layout)
        if not track_info:
            no_results_label = QLabel("No results found")
            no_results_label.setObjectName("no-playlist")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.most_played_layout.addWidget(no_results_label)
            return
        image_loader = ImageLoader(track_info)
        self.image_loaders.append(image_loader)
        image_loader.image_loaded.connect(lambda track, pixmap: self.update_track_image(self.most_played_layout, track, pixmap, track_info, rows=True))
        image_loader.finished.connect(lambda: self.on_image_loader_finished(image_loader))
        image_loader.start()

    def update_track_image(self, layout, track, pixmap, track_info, rows=False):
        if track["url"] in self.image_widgets:
            self.image_widgets[track["url"]].setPixmap(pixmap)

        # Only build the layout if it hasn't been built yet or if it's the initial load
        if layout.count() <= 1:  # Allow for header or empty layout
            self.clear_layout(layout)
            # Add header if applicable
            if layout == self.search_layout:
                header = QLabel(f"Results for '{self.inputfield.text().strip()}'")
                header.setObjectName("below-label")
                layout.addWidget(header)
            elif layout == self.artist_layout:
                header = QLabel(f"Popular songs for '{self.artist_inputfield.text().strip()}'")
                header.setObjectName("below-label")
                layout.addWidget(header)
            
            if rows:
                for i in range(0, len(track_info), 5):
                    row_layout = QHBoxLayout()
                    row_layout.setContentsMargins(10, 10, 10, 10)
                    row_layout.setSpacing(10)
                    for tr in track_info[i:i+5]:
                        main_child_layout = QVBoxLayout()
                        main_child_layout.setContentsMargins(0, 0, 0, 0)
                        main_child_layout.setAlignment(Qt.AlignCenter)
                        main_child_layout.setSpacing(10)
                        image = ClickableImage(track_id=tr["url"])
                        placeholder = QPixmap(140, 150)
                        placeholder.fill(Qt.gray)
                        image.setPixmap(placeholder)
                        image.setCursor(Qt.PointingHandCursor)
                        image.setAlignment(Qt.AlignCenter)
                        image.setObjectName("image-weekly")
                        image.clicked.connect(
                            lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]:
                            self.on_image_click(turl, tname, tartist)
                        )
                        self.image_widgets[tr["url"]] = image
                        main_child_layout.addWidget(image)
                        label_name = QLabel(tr["name"])
                        label_name.setObjectName("label-name")
                        label_name.setAlignment(Qt.AlignCenter)
                        label_name.setWordWrap(True)
                        label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                        main_child_layout.addWidget(label_name)
                        label_artist = QLabel(tr["artists"])
                        label_artist.setObjectName("artist-name")
                        label_artist.setAlignment(Qt.AlignCenter)
                        main_child_layout.addWidget(label_artist)
                        row_layout.addLayout(main_child_layout)
                    layout.addLayout(row_layout)
                layout.addStretch()
            else:
                tracks_layout = QHBoxLayout()
                tracks_layout.setContentsMargins(0, 0, 0, 0)
                tracks_layout.setSpacing(20)
                for tr in track_info:
                    main_child_layout = QVBoxLayout()
                    main_child_layout.setContentsMargins(0, 0, 0, 0)
                    main_child_layout.setAlignment(Qt.AlignCenter)
                    main_child_layout.setSpacing(10)
                    image = ClickableImage(track_id=tr["url"])
                    placeholder = QPixmap(140, 150)
                    placeholder.fill(Qt.gray)
                    image.setPixmap(placeholder)
                    image.setCursor(Qt.PointingHandCursor)
                    image.setAlignment(Qt.AlignCenter)
                    image.setObjectName("image-weekly")
                    image.clicked.connect(
                        lambda checked, turl=tr["url"], tname=tr["name"], tartist=tr["artists"]:
                        self.on_image_click(turl, tname, tartist)
                    )
                    self.image_widgets[tr["url"]] = image
                    main_child_layout.addWidget(image)
                    label_name = QLabel(tr["name"])
                    label_name.setObjectName("label-name")
                    label_name.setAlignment(Qt.AlignCenter)
                    label_name.setWordWrap(True)
                    label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    main_child_layout.addWidget(label_name)
                    label_artist = QLabel(tr["artists"])
                    label_artist.setObjectName("artist-name")
                    label_artist.setAlignment(Qt.AlignCenter)
                    main_child_layout.addWidget(label_artist)
                    tracks_layout.addLayout(main_child_layout)
                layout.addLayout(tracks_layout)
                layout.addStretch()

        # Update the specific track's image
        if track["url"] in self.image_widgets:
            self.image_widgets[track["url"]].setPixmap(pixmap)

    def show_home_search_error(self, error):
        self.clear_layout(self.main_track_layout)
        error_label = QLabel("Failed to fetch tracks")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.main_track_layout.addWidget(error_label)

    def show_weekly_more_search_error(self, error):
        self.clear_layout(self.weekly_more_layout)
        error_label = QLabel("Failed to fetch weekly top songs")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.weekly_more_layout.addWidget(error_label)

    def show_mood_songs_search_error(self, error):
        self.clear_layout(self.mood_songs_layout)
        error_label = QLabel("Failed to fetch mood songs")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.mood_songs_layout.addWidget(error_label)

    def show_mood_full_search_error(self, error):
        self.clear_layout(self.mood_full_layout)
        error_label = QLabel("Failed to fetch mood songs")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.mood_full_layout.addWidget(error_label)

    def show_new_releases_search_error(self, error):
        self.clear_layout(self.new_releases_layout)
        error_label = QLabel("Failed to fetch new releases")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.new_releases_layout.addWidget(error_label)

    def show_playlists_search_error(self, error):
        self.clear_layout(self.playlists_layout)
        error_label = QLabel("Failed to fetch playlists")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.playlists_layout.addWidget(error_label)

    def show_pop_search_error(self, error):
        self.clear_layout(self.pop_layout)
        error_label = QLabel("Failed to fetch pop songs")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.pop_layout.addWidget(error_label)

    def show_rock_search_error(self, error):
        self.clear_layout(self.rock_layout)
        error_label = QLabel("Failed to fetch rock songs")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.rock_layout.addWidget(error_label)

    def show_search_error(self, error):
        self.clear_layout(self.search_layout)
        error_label = QLabel("Failed to fetch results")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.search_layout.addWidget(error_label)

    def show_artist_search_error(self, error):
        self.clear_layout(self.artist_layout)
        error_label = QLabel("Failed to fetch results")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.artist_layout.addWidget(error_label)

    def show_most_played_search_error(self, error):
        self.clear_layout(self.most_played_layout)
        error_label = QLabel("Failed to fetch results")
        error_label.setObjectName("no-playlist")
        error_label.setAlignment(Qt.AlignCenter)
        self.most_played_layout.addWidget(error_label)

    def clear_layout(self, layout):
        # Clear image_widgets for tracks in this layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.layout():
                for j in range(item.layout().count()):
                    child_item = item.layout().itemAt(j)
                    if child_item.widget() and isinstance(child_item.widget(), ClickableImage):
                        track_url = child_item.widget().track_id
                        if track_url in self.image_widgets:
                            del self.image_widgets[track_url]
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout:
                self.clear_layout(child_layout)
                child_layout.deleteLater()

    def on_image_click(self, track_url, track_name, track_artist):
        if self.playbar:
            try:
                self.playbar.close_player()
            except RuntimeError:
                pass
            self.playbar = None
        self.playbar = PlayBar(self)
        self.layout().addWidget(self.playbar)
        self.playbar.update_track_info(track_name, track_artist, "3:45")
        self.playbar.play_track(track_url)

    def activate_tab(self, button, page, search_func=None):
        for btn in [
            self.home_button, self.search_button, self.recognize, self.artist,
            self.played, self.my_playlists, self.pop_genre, self.rock_genre, self.aboutbtn
        ]:
            btn.setObjectName("")
            btn.setStyleSheet("")
        button.setObjectName("active-btn")
        button.setStyleSheet("")
        self.pages.setCurrentWidget(page)
        if search_func and not self.closing:
            search_func()

    def load_stylesheet(self, filename):
        path = resource_path(filename) 
        file = QFile(path)
        if file.open(QFile.ReadOnly | QFile.Text):
            self.setStyleSheet(QTextStream(file).readAll())
            file.close()
        else:
            print(f"Warning: Could not load stylesheet {filename}")

    def closeEvent(self, event):
        self.closing = True  # Prevent new threads
        # Stop and clean up all threads
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait(5000)
        self.search_worker = None

        if self.artist_search_worker and self.artist_search_worker.isRunning():
            self.artist_search_worker.quit()
            self.artist_search_worker.wait(5000)
        self.artist_search_worker = None

        if self.recognition_worker and self.recognition_worker.isRunning():
            self.recognition_worker.quit()
            self.recognition_worker.wait(5000)
            self.recognition_worker.cleanup()
        self.recognition_worker = None

        for loader in self.image_loaders[:]:  # Iterate over a copy to allow removal
            if loader.isRunning():
                loader.quit()
                loader.wait(5000)
            self.image_loaders.remove(loader)
        self.image_loaders = []

        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Failed to start application: {e}")