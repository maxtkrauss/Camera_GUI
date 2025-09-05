import sys
import tifffile
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QSlider, QVBoxLayout, QWidget, QScrollArea
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.image_data = None

    def set_image_data(self, image_data):
        self.image_data = image_data
        height, width = image_data.shape
        bytes_per_line = width
        q_image = QImage(image_data.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        self.setPixmap(QPixmap.fromImage(q_image))

    def mouseMoveEvent(self, event):
        if self.image_data is not None:
            x = event.pos().x()
            y = event.pos().y()
            if 0 <= x < self.image_data.shape[1] and 0 <= y < self.image_data.shape[0]:
                value = self.image_data[y, x]
                self.setToolTip(f"X: {x}, Y: {y}, Value: {value}")

class TiffViewer(QMainWindow):
    def __init__(self, tiff_path):
        super().__init__()
        self.setWindowTitle("Multi-Dimensional TIFF Viewer")

        self.image_stack = tifffile.imread(tiff_path)
        self.current_index = 0

        # Inside TiffViewer.__init__ method
        self.image_label = ImageLabel()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.image_stack.shape[0] - 1)
        self.slider.valueChanged.connect(self.update_image)

        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.slider)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_image(0)

    def update_image(self, index):
        self.current_index = index
        image = self.image_stack[index]
        if image.ndim == 3 and image.shape[2] == 1:
            image = image[:, :, 0]
        self.image_label.set_image_data(image.astype(np.uint8))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = TiffViewer(sys.argv[1])  # Replace with your TIFF file path
    viewer.show()
    sys.exit(app.exec_())
