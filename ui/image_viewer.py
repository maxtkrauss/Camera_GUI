from PyQt5.QtWidgets import (QLabel, QMainWindow)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter

class ImageWindow(QMainWindow):
    def __init__(self, file_path):
        super().__init__()
        self.setWindowTitle("Image Viewer")

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.image_label)
        
        self.update_displayed_image(file_path)
        self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        # Call the base class implementation to ensure other key events are processed
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        self.update_displayed_image()

    def update_displayed_image(self, file_path=None):
        if file_path:
            self.original_pixmap = QPixmap(file_path)

        # Get current window size
        window_size = self.image_label.size()

        # Scale image with aspect ratio preserved
        scaled_pixmap = self.original_pixmap.scaled(
            window_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # Create black background pixmap
        black_bg = QPixmap(window_size)
        black_bg.fill(Qt.black)

        # Draw the scaled image centered onto black background
        painter = QPixmap(black_bg)
        painter.fill(Qt.black)

        # Compute offsets to center the image
        x_offset = (window_size.width() - scaled_pixmap.width()) // 2
        y_offset = (window_size.height() - scaled_pixmap.height()) // 2

        # paint the image at offset using QPainter
        final_pixmap = QPixmap(window_size)
        final_pixmap.fill(Qt.black)
        painter = QPainter(final_pixmap)
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
        painter.end()

        self.image_label.setPixmap(final_pixmap)
