from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPainter, QLinearGradient, QBrush, QFont, QPen, QColor
from PySide6.QtCore import Qt

class GradientLabel(QLabel):
    def __init__(self, text, font_size=40):
        super().__init__(text)
        self.setFont(QFont("Poppins", font_size, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#EE10B0"))  # Start color
        gradient.setColorAt(1, QColor(14, 158, 239, int(0.92 * 255)))  # End color with alpha

        painter.setPen(QPen(QBrush(gradient), 0))
        painter.setFont(self.font())
        painter.drawText(self.rect(), self.alignment(), self.text())
