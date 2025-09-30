import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QSlider, QTabWidget, QSpinBox, QScrollArea, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QPixmap, QImage, QPainter, QPen
import tifffile
import numpy as np

from controllers import DataCollectionController
from widgets import *

if __name__ == '__main__':
    app = QApplication(sys.argv)
    data_collection_widget = DataCollectionWidget()
    create_dataset_widget = CreateDatasetWidget()
    choose_dataset_widget = ChooseDataSetWidget()
    main_window = MainWindow(choose_dataset_widget, data_collection_widget, create_dataset_widget)
    controller = DataCollectionController(main_window, choose_dataset_widget, data_collection_widget, create_dataset_widget)
    main_window.show()
    sys.exit(app.exec_())