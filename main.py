from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QSizePolicy,QGraphicsDropShadowEffect
)
import sys
from PySide6.QtCore import Qt, QSize, QFile, QTextStream
from PySide6.QtGui import QIcon
from PySide6.QtGui import QFontDatabase, QFont,QColor
from components.gradient_label import GradientLabel  # Ensure this is implemented correctly

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
        sidebar.setObjectName("sidebar")
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
 
         # label
        self.recentlyplayed = QLabel("Recently Played")
        self.recentlyplayed.setObjectName("recent")
        sidebar.addWidget(self.recentlyplayed)
        
        # Buttons
        self.added=QPushButton("Recently Played")
        self.added.setIcon(QIcon("assets/svgs/time.svg"))
        self.added.setIconSize(QSize(20, 20))
        sidebar.addWidget(self.added)
        self.played=QPushButton("Most Played")
        self.played.setIcon(QIcon("assets/svgs/replay.svg"))
        self.played.setIconSize(QSize(20, 20))
        sidebar.addWidget(self.played)

           # label
        self.recentlyplayed = QLabel("General")
        self.recentlyplayed.setObjectName("recent")
        sidebar.addWidget(self.recentlyplayed)
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(190)
        sidebar_widget.setObjectName("sidebar")
        # Pages
        self.pages = QStackedWidget()

        self.home_page = QLabel("Welcome to Home Page 🎵")
        self.search_page = QLabel("Search Music 🔍")
        self.recognize_page = QLabel("Your recognized music 🎵")
        self.artist_page=QLabel("Artist 🎤")

        for page in [self.home_page, self.search_page, self.recognize_page,self.artist_page]:
            page.setObjectName("pageLabel")
            page.setAlignment(Qt.AlignCenter)
            self.pages.addWidget(page)
        
        # Connect buttons to pages
        self.home_button.clicked.connect(lambda: self.activate_tab(self.home_button, self.home_page))
        self.search_button.clicked.connect(lambda: self.activate_tab(self.search_button, self.search_page))
        self.recognize.clicked.connect(lambda: self.activate_tab(self.recognize, self.recognize_page))
        self.artist.clicked.connect(lambda: self.activate_tab(self.artist, self.artist_page))




        # Add to main layout
        main_layout.addWidget(sidebar_widget, 0)  # 2 show the sidebar width 
        main_layout.addWidget(self.pages, 3)  # 3 show the pages width
    def set_active_button(self, button):
            for btn in [self.home_button, self.search_button, self.recognize,self.artist]:
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
