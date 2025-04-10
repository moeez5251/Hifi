from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QSizePolicy
) 
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HiFi - Home")
        self.setMinimumSize(1000, 1000)
        self.setWindowIcon(QIcon("assets/Banner.png"))
        # Layouts
        main_layout = QHBoxLayout(self)

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.setSpacing(0)  # no space between widgets
        sidebar.setContentsMargins(0, 0, 0, 0)  # remove outer padding
        sidebar.setObjectName("sidebar")
        sidebar.setAlignment(Qt.AlignTop)
        sidebar.setSpacing(10)
        self.head = QLabel("HiFi")
        self.head.setObjectName("label")
        self.head.setFixedHeight(30)  # or 24 depending on font size
        sidebar.addWidget(self.head)

        self.home_button = QPushButton("Home")
        self.search_button = QPushButton("Search")
        self.library_button = QPushButton("Library")

        for btn in [self.home_button, self.search_button, self.library_button]:
            btn.setFixedHeight(30)
            sidebar.addWidget(btn)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(150)
        sidebar_widget.setObjectName("sidebar")

        # Pages
        self.pages = QStackedWidget()

        self.home_page = QLabel("Welcome to Home Page 🎵")
        self.search_page = QLabel("Search Music 🔍")
        self.library_page = QLabel("Your Library 📚")

        for page in [self.home_page, self.search_page, self.library_page]:
            page.setObjectName("pageLabel")
            page.setAlignment(Qt.AlignCenter)
            self.pages.addWidget(page)
        
        # Connect buttons to pages
        self.home_button.clicked.connect(lambda: self.pages.setCurrentWidget(self.home_page))
        self.search_button.clicked.connect(lambda: self.pages.setCurrentWidget(self.search_page))
        self.library_button.clicked.connect(lambda: self.pages.setCurrentWidget(self.library_page))

        # Add to main layout
        main_layout.addWidget(sidebar_widget,0) # 2 show the sidebar width 
        main_layout.addWidget(self.pages, 3) # 3 show the pages width
 
        # Apply styles
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: white;
                font-family: 'Segoe UI';
            }

            #sidebar{
                background-color:pink
            }

            QPushButton {
                background-color: orange;
                color: white;
                font-size: 16px;
                text-align: left;
                border: none;
                padding: 5px 10px
            }

          
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
