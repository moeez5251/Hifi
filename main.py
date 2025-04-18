from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QScrollArea,QSizePolicy,
)
import sys
from PySide6.QtCore import Qt, QSize, QFile, QTextStream,QUrl
from PySide6.QtGui import QIcon
from PySide6.QtGui import QFontDatabase, QFont,QColor
from components.gradient_label import GradientLabel
from PySide6.QtGui import QImage,QPixmap,QPainter,QPainterPath,QTransform
from components.playlist import get_pakistan_related_tracks
from io import BytesIO
from components.clickableimage import ClickableImage
from components.playbar import PlayBar
import requests
CLIENT_ID = "5c2fcd03261d47199284a7219dfc6fea"
CLIENT_SECRET = "58c0438e935348d78aa4facfc8ea8e48"

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
            print("Image was clicked!", track_url)
            
            # Remove the existing playbar if it exists and is not deleted
            if self.playbar is not None:
                try:
                    self.playbar.close_player()  # Call close_player to hide and delete
                except RuntimeError:
                    # Ignore if the playbar is already deleted
                    pass
                self.playbar = None  # Clear the reference

            # Create a new playbar
            self.playbar = PlayBar(self)  # Pass self as parent
            main_layout.addWidget(self.playbar)  # Add to the main layout
            self.playbar.update_track_info(track_name, artist_name, "3:45")
            self.playbar.play_track(track_url)  # Pass the track URL to play

        try:
            # token = get_access_token()
            tracks = get_pakistan_related_tracks()
            track_info = []
            for track in tracks["results"]:
                track_name = track['name']
                track_artists = track["artist_name"]
                track_image_url = track["album_image"]
                href = track['id']
                url=track['audio']
                track_info.append({
                    "name": track_name,
                    "artists": track_artists,
                    "album_image": track_image_url,
                    "href":href,
                    "url":url
                })
            print(track_info[0])
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
            print(e)
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
        
        self.weekly_more = QVBoxLayout()
        self.weekly_more.setSpacing(20)
        self.weekly_more.setAlignment(Qt.AlignTop)
        self.weekly_more.setContentsMargins(2, 0, 2, 0)
        
        below_label = QLabel()
        below_label.setText('<span>Weekly Top</span> <span style="color: #EE10B0;">Songs</span>')
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

        self.search_page = QLabel("Search Music 🔍")
        self.recognize_page = QLabel("Your recognized music 🎵")
        self.artist_page = QLabel("Artist 🎤")
        self.added_page = QLabel("Recently Played 🎵")
        self.played_page = QLabel("Most Played 🎵")
        self.log_page = QLabel("Logout 🎵")
        self.about_page = QLabel("About Us")
        for page in [self.search_page, self.recognize_page, self.artist_page, self.added_page, self.played_page, self.log_page, self.about_page]:
            page.setObjectName("pageLabel")
            page.setAlignment(Qt.AlignCenter)
            self.pages.addWidget(page)
        
        # Connect buttons to pages
        self.home_button.clicked.connect(lambda: self.activate_tab(self.home_button, home_scroll_area))
        self.search_button.clicked.connect(lambda: self.activate_tab(self.search_button, self.search_page))
        self.recognize.clicked.connect(lambda: self.activate_tab(self.recognize, self.recognize_page))
        self.artist.clicked.connect(lambda: self.activate_tab(self.artist, self.artist_page))
        self.added.clicked.connect(lambda: self.activate_tab(self.added, self.added_page))
        self.played.clicked.connect(lambda: self.activate_tab(self.played, self.played_page))
        self.log.clicked.connect(lambda: self.activate_tab(self.log, self.log_page))
        self.aboutbtn.clicked.connect(lambda: self.activate_tab(self.aboutbtn, self.about_page))
        button.clicked.connect(lambda: self.activate_tab(self.search_button, self.search_page))
        button_view.clicked.connect(lambda: self.activate_tab(self.home_button, weekly_scroll_area))

        # Add to content layout
        content_layout.addWidget(sidebar_widget, 0)
        content_layout.addWidget(self.pages, 3)
        
        # Add content layout to main layout
        main_layout.addLayout(content_layout)

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
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())