import os
import sys

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QSlider, QTabWidget, QSpinBox, QFileDialog, QMenu
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPixmap, QImage, QPainter, QPen, QPalette
import tifffile
import numpy as np

GT_IMAGE_PATH = r"F:\Morales\Exp7 - Macbeth LCD\scratch\cubert\image_0_cubert.tif"
GS_IMAGE_PATH = r"F:\Morales\Exp7 - Macbeth LCD\scratch\thorlabs\image_0_thorlabs.tif"

class MultiChannelTiffView (QWidget):
    def __init__(self, label_text: str, channel_range: tuple, format_string: str, discrete_labels: list | None=None, image_size=500):
        super().__init__()
        
        layout = QVBoxLayout()

        self.postprocessors = []
        self.format_string = format_string
        self.discrete_labels = discrete_labels
        self.image_size = image_size
        self.tiff_img = None

        self.view_label = QLabel(label_text)
        self.view_label.setFixedHeight(image_size)
        self.slider_label = QLabel("---")
        self.channel_slider = QSlider(Qt.Horizontal)
        self.channel_slider.setRange(channel_range[0], channel_range[1])
        self.channel_slider.valueChanged.connect(self.update_slider_label)
        self.channel_slider.valueChanged.connect(self.update_image)
        self.channel_slider.setFixedHeight(20)
        layout.addWidget(self.view_label)
        layout.addWidget(self.slider_label)
        layout.addWidget(self.channel_slider)

        self.update_slider_label()
        
        self.setLayout(layout)

    def update_slider_label (self):
        channel_index = self.channel_slider.value()
        if self.discrete_labels:
            insertion = self.discrete_labels[channel_index]
        else:
            insertion = channel_index
        new_label_text = self.format_string.replace("#", str(insertion))
        self.slider_label.setText(new_label_text)

    def update_image (self):
            if self.tiff_img.ndim == 3:
                img = self.tiff_img [self.channel_slider.value()]
            else:
                img = self.tiff_img
            img = np.clip(img, 0, None)
            norm = ((img - img.min()) / max(1e-5, img.max() - img.min()) * 255).astype(np.uint8)

            self.real_h, self.real_w = norm.shape
            qimg = QImage(norm.data, self.real_w, self.real_h, self.real_w, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimg).scaled(self.image_size, self.image_size, Qt.KeepAspectRatio)   

            qp = QPainter(pixmap)
            
            for p in self.postprocessors:
                p(qp, pixmap.width(), pixmap.height())

            qp.end()

            self.view_label.setPixmap(pixmap)

    def update_path (self, path):
        if not path or not os.path.exists(path):
                return
        self.tiff_img = tifffile.imread(path)
        self.update_image()

    def add_postprocessor (self, p):
        self.postprocessors.append(p)


class CropSelectionWidget (QWidget):
    def __init__(self, label_text: str, channel_range: tuple, format_string: str, discrete_labels: list | None=None, image_size: int=500):
        super().__init__()

        layout = QVBoxLayout()

        size_label = QLabel("Crop Region Size")
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(0, 100)
        self.size_slider.setFixedHeight(20)
        horizontal_offset_label = QLabel("Horizontal Offset")
        self.horizontal_offset_slider = QSlider(Qt.Horizontal)
        self.horizontal_offset_slider.setRange(0, 100)
        self.horizontal_offset_slider.setFixedHeight(20)
        vertical_offset_label = QLabel("Vertical Offset")
        self.vertical_offset_slider = QSlider(Qt.Horizontal)
        self.vertical_offset_slider.setRange(0, 100)
        self.vertical_offset_slider.setFixedHeight(20)
        self.tiff_viewer = MultiChannelTiffView(
            label_text=label_text, 
            channel_range=channel_range, 
            format_string=format_string, 
            discrete_labels=discrete_labels,
            image_size=image_size
        )
        self.crop_corner_x_label = QLabel("")
        self.crop_corner_y_label = QLabel("")
        self.crop_size_label = QLabel("")

        self.tiff_viewer.add_postprocessor(self._crop_box_drawer)

        self.size_slider.valueChanged.connect(self._on_slider_change)
        self.vertical_offset_slider.valueChanged.connect(self._on_slider_change)
        self.horizontal_offset_slider.valueChanged.connect(self._on_slider_change)

        layout.addWidget(size_label)
        layout.addWidget(self.size_slider)
        layout.addWidget(horizontal_offset_label)
        layout.addWidget(self.horizontal_offset_slider)
        layout.addWidget(vertical_offset_label)
        layout.addWidget(self.vertical_offset_slider)
        layout.addWidget(self.crop_corner_x_label)
        layout.addWidget(self.crop_corner_y_label)
        layout.addWidget(self.crop_size_label)
        layout.addWidget(self.tiff_viewer)

        self.setLayout(layout)

    def get_crop_size_percent(self):
        return self.size_slider.value()/100.0
    
    def get_horizontal_offset_percent(self):
        return self.horizontal_offset_slider.value()/100.0

    def get_vertical_offset_percent(self):
        return self.vertical_offset_slider.value()/100.0

    def update_path (self, path):
        self.tiff_viewer.update_path(path)

    def _on_slider_change (self):
        self.tiff_viewer.update_image()

    def _crop_box_drawer (self, painter: QPainter, w, h):
        crop_size_percent = self.get_crop_size_percent()
        horizontal_offset_percent = self.get_horizontal_offset_percent()
        vertical_offset_percent = self.get_vertical_offset_percent()

        x = int(horizontal_offset_percent*w)
        y = int(vertical_offset_percent*h)
        crop_size = int(crop_size_percent*w)

        self.crop_corner_x_label.setText(str(horizontal_offset_percent*self.tiff_viewer.real_w))
        self.crop_corner_y_label.setText(str(vertical_offset_percent*self.tiff_viewer.real_h))
        self.crop_size_label.setText(str(crop_size_percent*self.tiff_viewer.real_w))
    
        pen = QPen(QColor("red"), 3.0)
        painter.setPen(pen)
        painter.drawRect(x, y, crop_size, crop_size)

class CreateDatasetWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        top_layout = QVBoxLayout()
        middle_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        bottom_layout = QHBoxLayout()

        self.im_cropper = CropSelectionWidget(
            label_text="Thorlabs Image", 
            channel_range=(0,4), 
            format_string="Polarization: #", 
            discrete_labels=["0°", "45°", "90°", "135°", "Raw"]
        )
        self.gt_cropper = CropSelectionWidget(
            label_text="Cubert Image", 
            channel_range=(0,105), 
            format_string="Wavelength: # nm", 
            discrete_labels=[450 + int((i / 105) * (850 - 450)) for i in range(106)]
        )

        self.im_cropper.update_path(GS_IMAGE_PATH)
        self.gt_cropper.update_path(GT_IMAGE_PATH)

        layout.addLayout(top_layout)
        layout.addLayout(middle_layout)
        layout.addLayout(bottom_layout)

        middle_layout.addLayout(left_layout)
        middle_layout.addLayout(right_layout)

        left_layout.addWidget(self.im_cropper)
        right_layout.addWidget(self.gt_cropper)

        self.setLayout(layout)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CompuHSI Crop Utility")
        self.setGeometry(100, 100, 1100, 600)
        self.set_dark_theme()

        layout = QVBoxLayout()

        dataset_creation_widget = CreateDatasetWidget()

        layout.addWidget(dataset_creation_widget)

        self.setLayout(layout)

    def set_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.red)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.red)
        dark_palette.setColor(QPalette.ToolTipText, Qt.red)
        dark_palette.setColor(QPalette.Text, Qt.red)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.red)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        QApplication.setPalette(dark_palette)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MainWindow()
    gui.show()
    sys.exit(app.exec_())