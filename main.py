from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QScrollArea,QSizePolicy,
)
import sys
from PySide6.QtCore import Qt, QSize, QFile, QTextStream,QUrl
from PySide6.QtGui import QIcon
from PySide6.QtGui import QFontDatabase, QFont,QColor
from components.gradient_label import GradientLabel  # Ensure this is implemented correctly
from PySide6.QtGui import QImage,QPixmap,QPainter,QPainterPath,QTransform
from components.spotify import get_access_token,get_playlist_tracks
from io import BytesIO
from components.clickableimage import ClickableImage
from components.playbar import PlayBar
import requests
CLIENT_ID = "5c2fcd03261d47199284a7219dfc6fea"
CLIENT_SECRET = "58c0438e935348d78aa4facfc8ea8e48"

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        font_id = QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf")  # Poppins font
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            custom_font = QFont(font_family,14)
            self.setFont(custom_font)
        self.setWindowTitle("HiFi")
        self.setMinimumSize(1000, 1000)
        self.setWindowIcon(QIcon("assets/Logo.png"))
        self.load_stylesheet("style.css")



        def on_image_click(track_id):
            print("Image was clicked!",track_id)
            track_name = "Track Name"
            artist = "Artist Name"

            # Remove previous bar if exists
            if hasattr(main_layout, "play_bar") and main_layout.play_bar:
                main_layout.removeWidget(main_layout.play_bar)
                main_layout.play_bar.deleteLater()

            # Create new play bar and add to layout
            main_layout.play_bar = PlayBar(track_name, artist)
            main_layout.addWidget(main_layout.play_bar)
        # Layouts
        main_layout = QHBoxLayout(self)

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.setSpacing(6)  # space between widgets
        sidebar.setAlignment(Qt.AlignTop)
        sidebar.setSpacing(20)
        sidebar.setContentsMargins(20, 20, 20, 0)

        # logo
        self.head = GradientLabel("HiFi", font_size=25)
        self.head.setObjectName("label")
        sidebar.addWidget(self.head)
        
        # label
        self.menu = QLabel("Menu")
        self.menu.setObjectName("Menu")
        sidebar.addWidget(self.menu)
        
        # butttons
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
        self.artist=QPushButton("Artist")
        self.artist.setIcon(QIcon("assets/svgs/Artist.svg"))
        self.artist.setIconSize(QSize(20, 20))
        for btn in [self.home_button, self.search_button, self.recognize,self.artist]:
            sidebar.addWidget(btn)
            btn.setCursor(Qt.PointingHandCursor)
 
         # label
        self.recentlyplayed = QLabel("Recently Played")
        self.recentlyplayed.setObjectName("recent")
        sidebar.addWidget(self.recentlyplayed)
        
        # Buttons
        self.added=QPushButton("Recently Played")
        self.added.setIcon(QIcon("assets/svgs/time.svg"))
        self.added.setIconSize(QSize(20, 20))
        self.added.setCursor(Qt.PointingHandCursor)
        sidebar.addWidget(self.added)
        self.played=QPushButton("Most Played")
        self.played.setIcon(QIcon("assets/svgs/replay.svg"))
        self.played.setIconSize(QSize(20, 20))
        self.played.setCursor(Qt.PointingHandCursor)
        sidebar.addWidget(self.played)
        # label
        self.recentlyplayed = QLabel("General")
        self.recentlyplayed.setObjectName("recent")
        sidebar.addWidget(self.recentlyplayed)
        #button
        self.log=QPushButton("Logout")
        self.log.setIcon(QIcon("assets/svgs/logout.svg"))
        self.log.setIconSize(QSize(20, 20))
        self.log.setCursor(Qt.PointingHandCursor)
        sidebar.addWidget(self.log)

        
        sidebar.about=QLabel("About Us")
        sidebar.about.setObjectName("recent")
        sidebar.addWidget(sidebar.about)
        self.aboutbtn=QPushButton("About Us")
        self.aboutbtn.setIcon(QIcon("assets/svgs/about.svg"))
        self.aboutbtn.setIconSize(QSize(20, 20))
        self.aboutbtn.setCursor(Qt.PointingHandCursor)
        sidebar.addWidget(self.aboutbtn)
        
        # sidebar widget
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(190)
        sidebar_widget.setObjectName("sidebar")

        # Pages
        self.pages = QStackedWidget()

        # home page
        home = QVBoxLayout()
        home.setSpacing(20)
        home.setAlignment(Qt.AlignTop)
        home.setContentsMargins(2, 0, 2, 0)
        # Use QLabel for the background image
        background_label = QLabel()
        image = QImage('assets/Banner.png')
        if image.isNull():
            background_label.setStyleSheet("background: red;")  # Fallback to see widget
        else:
            # Mirror the image horizontally (left-to-right flip)
            transform = QTransform().scale(-1, 1)
            mirrored_image =image.transformed(transform, Qt.SmoothTransformation)

            window_width = self.width() if self.width() > 0 else 800
            image_height = int(self.height() * 0.5) if self.height() > 0 else 400

            scaled_pixmap = QPixmap.fromImage(mirrored_image).scaled(
                window_width, image_height,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

            # Create transparent pixmap for rounded + filter
            final_pixmap = QPixmap(window_width, image_height)
            final_pixmap.fill(Qt.transparent)

            painter = QPainter(final_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # Rounded mask
            path = QPainterPath()
            radius = 10
            path.addRoundedRect(0, 0, window_width, image_height, radius, radius)
            painter.setClipPath(path)

            # Draw image
            painter.drawPixmap(0, 0, scaled_pixmap)

            # 🔥 Apply filter: semi-transparent black overlay
            overlay_color = QColor(0, 0, 0, 100)  # RGBA: A = opacity (0–255) 
            painter.fillRect(final_pixmap.rect(), overlay_color)

            painter.end()

            # Apply to QLabel
            background_label.setPixmap(final_pixmap)
            background_label.setScaledContents(True)
        # Layout for labels on top of background
        content_layout = QVBoxLayout(background_label)
        content_layout.setContentsMargins(20,120, 0, 0)
        content_layout.setAlignment(Qt.AlignTop)
        content_layout.setSpacing(0)
        # Add labels in front of the background
        label1 = QLabel() 
        label1.setObjectName("label1")
        label1.setText('<span style="font-weight: bold;">All the <span style="color: #EE10B0;">Best Songs</span> <br> in One Place</span>')
        content_layout.addWidget(label1)

        label2 = QLabel()
        label2.setText('<span>On our app, you can access an amazing collection of popular and new songs</span> <br> <span>Stream your favorite tracks in high quality and enjoy without interruptions </span> <br> <span> Whatever your taste in music, we have it all for you! </span>')
        label2.setObjectName("label2")
        content_layout.addWidget(label2)
        button=QPushButton("Discover Now")
        button.setCursor(Qt.PointingHandCursor)
        button.setObjectName("discover")
        button.setMaximumWidth(150)
        button.setFixedHeight(60)
        content_layout.addWidget(button)
 
        # Add background label to home layout
        home.addWidget(background_label)

        # Add more content below
        below_label = QLabel()
        below_label.setText('<span>Weekly Top</span> <span style="color: #EE10B0;">Songs</span>')
        below_label.setObjectName("below-label")
        home.addWidget(below_label)

        # Tracks Layout 
        main_track_layout=QHBoxLayout()
        main_track_layout.setContentsMargins(10,10,10,10)
        try:
            token=get_access_token()
            tracks=get_playlist_tracks("4SPLJ3VJJF4eIO0eciwQ8Y",token)
            track_info = []
            for track in tracks["items"]:
                track_name = track['track']['name']
                track_artists = ", ".join([artist['name'] for artist in track['track']['artists']])
                track_image_url = track['track']['album']['images'][0]['url']  # Get the album artwork
                track=track['track']['id']
                track_info.append({
                    "name": track_name,
                    "artists": track_artists,
                    "album_image": track_image_url,
                    "href":track
                })
            print(track_info[0])
            for tr in track_info[5:10]:
                main_child_layout=QVBoxLayout()
                main_child_layout.setContentsMargins(0,0,0,0)
                main_child_layout.setAlignment(Qt.AlignCenter)
                main_child_layout.setSpacing(10)
                image=ClickableImage(track_id=tr["href"])
                image_url = tr["album_image"]
                response = requests.get(image_url)
                response.raise_for_status()
                image_data = BytesIO(response.content)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data.read())
                pixmap = pixmap.scaled(140, 150, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

                # Create a new pixmap with rounded corners
                rounded_pixmap = QPixmap(140, 150)
                rounded_pixmap.fill(Qt.transparent)  # Transparent background
                painter = QPainter(rounded_pixmap)
                path = QPainterPath()
                path.addRoundedRect(0, 0, 140, 150, 10, 10)  # 10px radius for corners
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                image.setPixmap(rounded_pixmap)
                image.setCursor(Qt.PointingHandCursor)
                image.setAlignment(Qt.AlignCenter)
                image.setObjectName("image-weekly")
                image.clicked.connect(on_image_click)
                main_child_layout.addWidget(image)
                label_name=QLabel(tr["name"])
                label_name.setObjectName("label-name")
                label_name.setAlignment(Qt.AlignCenter)
                label_name.setWordWrap(True)  # Enable wrapping
                label_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                main_child_layout.addWidget(label_name)
                label_name=QLabel(tr["artists"])
                label_name.setObjectName("artist-name")
                label_name.setAlignment(Qt.AlignCenter)
                main_child_layout.addWidget(label_name)

                main_track_layout.addLayout(main_child_layout)
            button_view=QPushButton("Show More")
            button_view.setIcon(QIcon("assets/svgs/more.svg"))
            button_view.setCursor(Qt.PointingHandCursor)
            button_view.setObjectName("button-view")
            button_view.setIconSize(QSize(40,40))
            main_track_layout.addWidget(button_view)
        except Exception as e:
            print(e)
            not_label=QLabel("No Playlist Found")
            not_label.setObjectName("no-playlist")
            not_label.setAlignment(Qt.AlignCenter)
            main_track_layout.addWidget(not_label)
        # Wrap home layout in QWidget
        home.addLayout(main_track_layout)
        homepage_widget = QWidget()
        homepage_widget.setLayout(home)
        homepage_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Scroll area
        home_scroll_area = QScrollArea()
        home_scroll_area.setWidget(homepage_widget)
        home_scroll_area.setWidgetResizable(True)
        home_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        home_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        home_scroll_area.setStyleSheet("QScrollArea { border: none; }")

        # Add scroll area to pages
        self.pages.addWidget(home_scroll_area)
        
        
        self.search_page = QLabel("Search Music 🔍")
        self.recognize_page = QLabel("Your recognized music 🎵")
        self.artist_page=QLabel("Artist 🎤")
        self.added_page=QLabel("Recently Played 🎵")
        self.played_page=QLabel("Most Played 🎵")
        self.log_page=QLabel("Logout 🎵")
        self.about_page=QLabel("About Us")
        for page in [self.search_page, self.recognize_page,self.artist_page,self.added_page,self.played_page,self.log_page,self.about_page]:
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



        # Add to main layout
        main_layout.addWidget(sidebar_widget, 0)  # 2 show the sidebar width 
        main_layout.addWidget(self.pages, 3)  # 3 show the pages width
    def set_active_button(self, button):
            for btn in [self.home_button, self.search_button, self.recognize,self.artist,self.added,self.played,self.log,self.aboutbtn]:
                btn.setObjectName("")  # Remove old objectName
                btn.setStyleSheet("")  # Reset styles if necessary
                button.setObjectName("active-btn")
                button.setStyleSheet("")  # Re-apply stylesheet to trigger the change
    def activate_tab(self, button, page):
            self.set_active_button(button)
            self.pages.setCurrentWidget(page)
    def load_stylesheet(self, file_path):
        """Load and apply external CSS file"""
        file = QFile(file_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stylesheet = QTextStream(file).readAll()
            self.setStyleSheet(stylesheet)
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
