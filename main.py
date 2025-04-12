from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QScrollArea,QSizePolicy,
)
import sys
from PySide6.QtCore import Qt, QSize, QFile, QTextStream
from PySide6.QtGui import QIcon
from PySide6.QtGui import QFontDatabase, QFont,QColor
from components.gradient_label import GradientLabel  # Ensure this is implemented correctly
from PySide6.QtGui import QImage,QPixmap
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        font_id = QFontDatabase.addApplicationFont("assets/fonts/Poppins-Regular.ttf")  # Poppins font
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            custom_font = QFont(font_family,14)
            self.setFont(custom_font)
        self.setWindowTitle("HiFi - Home")
        self.setMinimumSize(1000, 1000)
        self.setWindowIcon(QIcon("assets/Banner.png"))
        self.load_stylesheet("style.css")

        
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
        home.setContentsMargins(0, 0, 0, 0)

        # Use QLabel for the background image
        background_label = QLabel()
        image = QImage('assets/Banner.png')
        if image.isNull():
            print("Error: Failed to load 'assets/Banner.png'")
            background_label.setStyleSheet("background: red;")  # Fallback to see widget
        else:
            # Calculate size based on window width and image aspect ratio
            window_width = self.width() if self.width() > 0 else 800  # Fallback width
            aspect_ratio = image.width() / image.height()
            image_height = int(window_width / aspect_ratio)  # Height to show full image
            background_label.setFixedSize(1500, image_height)
            pixmap = QPixmap.fromImage(image).scaled(window_width, image_height, Qt.KeepAspectRatio)
            background_label.setPixmap(pixmap)
            background_label.setScaledContents(True)  # Scale pixmap to label size
            background_label.setStyleSheet("border: 1px solid blue;")  # Debug border
            print(f"Window width: {window_width}, Image size: {image.width()}x{image.height()}, Label size: {window_width}x{image_height}")

        # Layout for labels on top of background
        content_layout = QVBoxLayout(background_label)
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Add labels in front of the background
        label1 = QLabel("Welcome to the Home Page!")
        label1.setStyleSheet("font-size: 18px; color: white; background: transparent;")
        content_layout.addWidget(label1)

        label2 = QLabel("Explore our features below")
        label2.setStyleSheet("font-size: 16px; color: white; background: transparent;")
        content_layout.addWidget(label2)

        # Add background label to home layout
        home.addWidget(background_label)

        # Add more content below
        below_label = QLabel("Additional Content Here")
        below_label.setStyleSheet("font-size: 16px; color: white;")
        home.addWidget(below_label)

        # Wrap home layout in QWidget
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
        
        for page in [self.search_page, self.recognize_page,self.artist_page,self.added_page,self.played_page,self.log_page]:
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




        # Add to main layout
        main_layout.addWidget(sidebar_widget, 0)  # 2 show the sidebar width 
        main_layout.addWidget(self.pages, 3)  # 3 show the pages width
    def set_active_button(self, button):
            for btn in [self.home_button, self.search_button, self.recognize,self.artist,self.added,self.played,self.log]:
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
