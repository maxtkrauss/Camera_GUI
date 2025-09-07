import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QSlider, QTabWidget, QSpinBox, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QPixmap, QImage, QPainter, QPen
import tifffile
import numpy as np

class CompuHSIDataset:
    base_dir = ""
    dark_frame_dir = ""
    gt_cam_name = ""
    im_cam_name = ""
    gt_crop_size = 120
    gt_crop_offset = (0,0)
    im_crop_size = 660
    im_crop_offset = (0,0)
    test_size = 0
    train_size = 0
    test_assignment_probability = 20


class StatusIndicator (QWidget):

    OK = 0
    WARNING = 1
    ERROR = 2

    def __init__(self):
        super().__init__()
        # Status indicator layout
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("---")
        status_layout.addWidget(self.status_label)

        self.setLayout(status_layout)

    def _get_stylesheet (self, status_code):
        match (status_code):
            case self.OK:
                return "background-color: green; color: white; padding: 5px; border-radius: 3px;"
            case self.WARNING:
                return "background-color: yellow; color: white; padding: 5px; border-radius: 3px;"
            case self.ERROR:
                return "background-color: red; color: white; padding: 5px; border-radius: 3px;"

    def update_status (self, msg, code):
        self.status_label.setText(f"Status: {msg}")
        self.status_label.setStyleSheet(self._get_stylesheet(code))
        QApplication.processEvents()  # Force UI update

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
            img = np.clip(img, 0, None)
            norm = ((img - img.min()) / max(1e-5, img.max() - img.min()) * 255).astype(np.uint8)

            h, w = norm.shape
            qimg = QImage(norm.data, w, h, w, QImage.Format_Grayscale8)
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

class ChooseDataSetWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.directoryInput = QLineEdit()

        button_layout = QHBoxLayout()
        self.existing_dataset_button = QPushButton("Select An Existing Dataset")
        self.new_dataset_button = QPushButton("Create a new dataset")
        button_layout.addWidget(self.existing_dataset_button)
        button_layout.addWidget(self.new_dataset_button)

        layout.addWidget(self.directoryInput)
        layout.addLayout(button_layout)        

        self.setLayout(layout)

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

        im_final_size_label = QLabel("Final Size for Originals")
        self.im_final_size_input = QLineEdit("660")
        gt_final_size_label = QLabel("Final Size for Ground Truth")
        self.gt_final_size_input = QLineEdit("120")

        self.alignment_aid_button = QPushButton("Show Alignment Aid")

        test_assignment_probability_label = QLabel("Test Assignment Probability")
        self.test_assignment_probability_input = QLineEdit("20")

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

        self.proceed_button = QPushButton("Proceed to Dark Frame Collection")

        self.im_cropper.update_path('/home/matthew-morales/Downloads/image_9_thorlabs.tif')
        self.gt_cropper.update_path('/home/matthew-morales/Downloads/image_9_cubert.tif')

        layout.addLayout(top_layout)
        layout.addLayout(middle_layout)
        layout.addLayout(bottom_layout)

        top_layout.addWidget(im_final_size_label)
        top_layout.addWidget(self.im_final_size_input)
        top_layout.addWidget(gt_final_size_label)
        top_layout.addWidget(self.gt_final_size_input)
        top_layout.addWidget(test_assignment_probability_label)
        top_layout.addWidget(self.test_assignment_probability_input)

        middle_layout.addLayout(left_layout)
        middle_layout.addLayout(right_layout)

        top_layout.addWidget(self.alignment_aid_button)
        left_layout.addWidget(self.im_cropper)
        right_layout.addWidget(self.gt_cropper)
        bottom_layout.addWidget(self.proceed_button)

        self.setLayout(layout)

class DataCollectionWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Folder & dark frame selection
        folder_layout = QHBoxLayout()

        # Exposure controls
        exposure_layout = QHBoxLayout()
        self.exposure_tl_input = QSpinBox()
        self.exposure_tl_input.setRange(10, 10000)
        self.exposure_tl_input.setValue(400)
        self.exposure_tl_input.setSuffix(" ms")

        self.exposure_cb_input = QSpinBox()
        self.exposure_cb_input.setRange(10, 10000)
        self.exposure_cb_input.setValue(550)
        self.exposure_cb_input.setSuffix(" ms")

        # Add auto exposure buttons
        auto_exposure_tl_btn = QPushButton("Auto TL Exposure")
        
        auto_exposure_cb_btn = QPushButton("Auto CB Exposure")
        
        auto_exposure_both_btn = QPushButton("Auto Both Exposures")

        exposure_layout.addWidget(QLabel("Thorlabs Exposure:"))
        exposure_layout.addWidget(self.exposure_tl_input)
        exposure_layout.addWidget(auto_exposure_tl_btn)
        exposure_layout.addWidget(QLabel("Cubert Exposure:"))
        exposure_layout.addWidget(self.exposure_cb_input)
        exposure_layout.addWidget(auto_exposure_cb_btn)
        exposure_layout.addWidget(auto_exposure_both_btn)

        status_indicator = StatusIndicator()

        # Tabs for Manual and Auto
        self.tabs = QTabWidget()
        self.manual_tab = QWidget()
        self.auto_tab = QWidget()
        self.tabs.addTab(self.manual_tab, "Manual Mode")
        self.tabs.addTab(self.auto_tab, "Auto Mode")

        self.init_manual_tab()
        self.init_auto_tab()

        layout.addLayout(folder_layout)
        layout.addLayout(exposure_layout)
        layout.addWidget(status_indicator)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def init_manual_tab(self):
        layout = QVBoxLayout()
        capture_btn = QPushButton("Capture Image")

        image_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        im_view = MultiChannelTiffView(
            label_text="Thorlabs Image", 
            channel_range=(0,4), 
            format_string="Polarization: #", 
            discrete_labels=["0°", "45°", "90°", "135°", "Raw"]
        )
        left_layout.addWidget(im_view)

        im_view.update_path('/home/matthew-morales/Downloads/image_9_thorlabs.tif')

        gt_view = MultiChannelTiffView(
            label_text="Cubert Image", 
            channel_range=(0,105), 
            format_string="Wavelength: # nm", 
            discrete_labels=[450 + int((i / 105) * (850 - 450)) for i in range(106)]
        )
        right_layout.addWidget(gt_view)

        gt_view.update_path('/home/matthew-morales/Downloads/image_9_cubert.tif')

        image_layout.addLayout(left_layout)
        image_layout.addLayout(right_layout)

        layout.addWidget(capture_btn)
        layout.addLayout(image_layout)
        self.manual_tab.setLayout(layout)

    def init_auto_tab(self):
        layout = QVBoxLayout()

        self.dataset_input = QLineEdit()
        choose_dataset_btn = QPushButton("Select Dataset Folder")

        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("Interval (s)")

        self.exposure_center_val = QLineEdit()
        self.exposure_center_val.setPlaceholderText("ms")

        self.alphebetical_offset_input = QLineEdit()
        self.alphebetical_offset_input.setPlaceholderText("0")
        self.alphebetical_offset_input.setText(str(0))

        start_btn = QPushButton("Start Auto Capture")
        stop_btn = QPushButton("Stop Auto Capture")

        layout.addWidget(self.dataset_input)
        layout.addWidget(choose_dataset_btn)
        layout.addWidget(self.interval_input)
        layout.addWidget(self.exposure_center_val)
        layout.addWidget(self.alphebetical_offset_input)
        layout.addWidget(start_btn)
        layout.addWidget(stop_btn)

        self.auto_tab.setLayout(layout)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.state = 1

        self.setWindowTitle("CompuHSI Data Collection")
        self.setGeometry(100, 100, 1100, 600)
        self.set_dark_theme()

        layout = QVBoxLayout()

        match (self.state):
            case 0:
                data_collection_widget = DataCollectionWidget()
                layout.addWidget(data_collection_widget)
            case 1:
                date_creation_widget = CreateDatasetWidget()
                layout.addWidget(date_creation_widget)

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