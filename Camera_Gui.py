# UnifiedCameraGUI.py
# Dark-themed, unified camera GUI for Thorlabs & Cubert systems

import sys
import os
import time
import tifffile
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QLineEdit, QSlider, QTabWidget, QMessageBox, QSpinBox, QMainWindow
)
from PyQt5.QtCore import Qt, QTimer, QSemaphore
from PyQt5.QtGui import QPixmap, QImage, QPalette, QColor, QPainter

import scene_imager as si
import logging

# Store the original stdout
original_stdout = sys.stdout

# Open a file in write mode ('w') or append mode ('a')
# 'w' will overwrite the file each time, 'a' will append to it
log_file = open("output.log", "w")

# Redirect sys.stdout to the file
sys.stdout = log_file

def get_file_at_alphebetical_index (directory, index=0):
    # Get all entries and sort them alphabetically
    all_items = sorted(os.listdir(directory))

    # Get the first item, if it exists
    if all_items:
        return os.path.join(directory, all_items[index])
    else:
        return None

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
        print(file_path)
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


class UnifiedCameraGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unified Camera GUI")
        self.setGeometry(100, 100, 1100, 600)
        self.set_dark_theme()

        # Camera and image vars
        self.cam_tl = si.setup_thorlabs_cam()
        self.acq_ctx, self.proc_ctx, _ = si.setup_cubert_cam()
        self.dark_tl = None
        self.dark_cb = None
        self.image_counter = 0

        self.dataset_folder = None
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.capture_auto_image)

        self.auto_timer_semph = QSemaphore(1)

        # Build GUI
        self.init_ui()

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

    def init_ui(self):
        layout = QVBoxLayout()

        # Folder & dark frame selection
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        choose_folder_btn = QPushButton("Select Save Folder")
        choose_folder_btn.clicked.connect(self.select_save_folder)

        dark_tl_btn = QPushButton("Thorlabs Dark Frame")
        dark_tl_btn.clicked.connect(self.load_dark_tl)
        dark_cb_btn = QPushButton("Cubert Dark Frame")
        dark_cb_btn.clicked.connect(self.load_dark_cb)

        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(choose_folder_btn)
        folder_layout.addWidget(dark_tl_btn)
        folder_layout.addWidget(dark_cb_btn)

        # Exposure controls
        exposure_layout = QHBoxLayout()
        self.exposure_tl_input = QSpinBox()
        self.exposure_tl_input.setRange(10, 10000)
        self.exposure_tl_input.setValue(400)
        self.exposure_tl_input.setSuffix(" ms")
        self.exposure_tl_input.valueChanged.connect(lambda val: self.cam_tl.set_exposure(val / 1000.0))

        self.exposure_cb_input = QSpinBox()
        self.exposure_cb_input.setRange(10, 10000)
        self.exposure_cb_input.setValue(550)
        self.exposure_cb_input.setSuffix(" ms")
        self.exposure_cb_input.valueChanged.connect(lambda val: setattr(self.acq_ctx, 'integration_time', val))

        # Add auto exposure buttons
        auto_exposure_tl_btn = QPushButton("Auto TL Exposure")
        auto_exposure_tl_btn.clicked.connect(self.auto_expose_thorlabs)
        
        auto_exposure_cb_btn = QPushButton("Auto CB Exposure")
        auto_exposure_cb_btn.clicked.connect(self.auto_expose_cubert)
        
        auto_exposure_both_btn = QPushButton("Auto Both Exposures")
        auto_exposure_both_btn.clicked.connect(self.auto_expose_both)

        exposure_layout.addWidget(QLabel("Thorlabs Exposure:"))
        exposure_layout.addWidget(self.exposure_tl_input)
        exposure_layout.addWidget(auto_exposure_tl_btn)
        exposure_layout.addWidget(QLabel("Cubert Exposure:"))
        exposure_layout.addWidget(self.exposure_cb_input)
        exposure_layout.addWidget(auto_exposure_cb_btn)
        exposure_layout.addWidget(auto_exposure_both_btn)

        # Status indicator layout
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("background-color: green; color: white; padding: 5px; border-radius: 3px;")
        status_layout.addWidget(self.status_label)

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
        layout.addLayout(status_layout)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def update_status(self, message, is_waiting=True):
        """Update the status indicator with message and color"""
        self.status_label.setText(f"Status: {message}")
        if is_waiting:
            self.status_label.setStyleSheet("background-color: red; color: white; padding: 5px; border-radius: 3px;")
        else:
            self.status_label.setStyleSheet("background-color: green; color: white; padding: 5px; border-radius: 3px;")
        QApplication.processEvents()  # Force UI update

    def auto_expose_thorlabs(self):
        try:
            self.update_status("Calculating Thorlabs exposure...", True)
            
            # Run auto exposure for Thorlabs
            new_exposure = si.auto_exposure_thorlabs(self.cam_tl)
            
            # Update the GUI spinbox with the new value
            self.exposure_tl_input.setValue(new_exposure)
            
            self.update_status("Thorlabs exposure set successfully", False)
            return True
        except Exception as e:
            self.update_status(f"Thorlabs exposure failed: {str(e)}", True)
            # QMessageBox.warning(self, "Error", f"Auto exposure failed: {str(e)}")
            return False

    def auto_expose_cubert(self):
        try:
            self.update_status("Calculating Cubert exposure...", True)
            
            # Run auto exposure for Cubert
            new_exposure, _ = si.auto_exposure_cubert(self.acq_ctx, self.proc_ctx)
            
            # Update the GUI spinbox with the new value
            self.exposure_cb_input.setValue(int(new_exposure))
            
            self.update_status("Cubert exposure set successfully", False)
            return True
        except Exception as e:
            self.update_status(f"Cubert exposure failed: {str(e)}", True)
            # QMessageBox.warning(self, "Error", f"Auto exposure failed: {str(e)}")
            return False

    def auto_expose_both(self):
        try:
            self.update_status("Calculating exposures for both cameras...", True)
            
            # Run auto exposure for both cameras
            new_tl_exposure = si.auto_exposure_thorlabs(self.cam_tl)
            new_cb_exposure, cb_success = si.auto_exposure_cubert(self.acq_ctx, self.proc_ctx)
            
            # Update the GUI spinboxes with the new values
            self.exposure_tl_input.setValue(new_tl_exposure)
            self.exposure_cb_input.setValue(int(new_cb_exposure))
            
            self.update_status("Both exposures set successfully", False)
            return cb_success
        except Exception as e:
            self.update_status(f"Auto exposure failed: {str(e)}", True)
            QMessageBox.warning(self, "Error", f"Auto exposure failed: {str(e)}")
            return False

    def init_manual_tab(self):
        layout = QVBoxLayout()
        capture_btn = QPushButton("Capture Image")
        capture_btn.clicked.connect(self.capture_manual_image)

        image_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.tl_label = QLabel("Thorlabs Image")
        self.slider_tl_label = QLabel("Polarization: 0°")
        self.slider_tl = QSlider(Qt.Horizontal)
        self.slider_tl.setRange(0, 4)
        self.slider_tl.setFixedHeight(20)
        self.slider_tl.valueChanged.connect(self.update_tl_slider_label)
        self.slider_tl.valueChanged.connect(lambda: self.update_display(self.last_tl_path, self.tl_label, self.slider_tl.value(), True))
        left_layout.addWidget(self.tl_label)
        left_layout.addWidget(self.slider_tl_label)
        left_layout.addWidget(self.slider_tl)

        self.cb_label = QLabel("Cubert Image")
        self.slider_cb_label = QLabel("Wavelength: 450 nm")
        self.slider_cb = QSlider(Qt.Horizontal)
        self.slider_cb.setRange(0, 105)
        self.slider_cb.setFixedHeight(20)
        self.slider_cb.valueChanged.connect(self.update_cb_slider_label)
        self.slider_cb.valueChanged.connect(lambda: self.update_display(self.last_cb_path, self.cb_label, self.slider_cb.value(), False))
        right_layout.addWidget(self.cb_label)
        right_layout.addWidget(self.slider_cb_label)
        right_layout.addWidget(self.slider_cb)

        image_layout.addLayout(left_layout)
        image_layout.addLayout(right_layout)

        layout.addWidget(capture_btn)
        layout.addLayout(image_layout)
        self.manual_tab.setLayout(layout)

    def update_tl_slider_label(self):
        labels = ["0°", "45°", "90°", "135°", "Raw"]
        idx = self.slider_tl.value()
        self.slider_tl_label.setText(f"Polarization: {labels[idx]}")

    def update_cb_slider_label(self):
        idx = self.slider_cb.value()
        wavelength = 450 + int((idx / 105) * (850 - 450))
        self.slider_cb_label.setText(f"Wavelength: {wavelength} nm")

    def init_auto_tab(self):
        layout = QVBoxLayout()

        self.dataset_input = QLineEdit()
        choose_dataset_btn = QPushButton("Select Dataset Folder")
        choose_dataset_btn.clicked.connect(self.select_dataset_folder)

        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("Interval (s)")

        self.exposure_center_val = QLineEdit()
        self.exposure_center_val.setPlaceholderText("ms")

        self.alphebetical_offset_input = QLineEdit()
        self.alphebetical_offset_input.setPlaceholderText("0")
        self.alphebetical_offset_input.setText(str(0))

        start_btn = QPushButton("Start Auto Capture")
        start_btn.clicked.connect(self.start_auto_capture)
        stop_btn = QPushButton("Stop Auto Capture")
        stop_btn.clicked.connect(self.stop_auto_capture)

        layout.addWidget(self.dataset_input)
        layout.addWidget(choose_dataset_btn)
        layout.addWidget(self.interval_input)
        layout.addWidget(self.exposure_center_val)
        layout.addWidget(self.alphebetical_offset_input)
        layout.addWidget(start_btn)
        layout.addWidget(stop_btn)

        self.auto_tab.setLayout(layout)

    def select_save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        if folder:
            self.folder_input.setText(folder)
            si.thorlabs_image_folder = os.path.join(folder, "thorlabs")
            si.cubert_image_folder = os.path.join(folder, "cubert")
            os.makedirs(si.thorlabs_image_folder, exist_ok=True)
            os.makedirs(si.cubert_image_folder, exist_ok=True)

    def select_dataset_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Dataset Folder")
        if folder:
            self.dataset_input.setText(folder)
            self.dataset_folder = folder
            self.open_image_window()

    def open_image_window(self):
        first_image = get_file_at_alphebetical_index(self.dataset_folder)
        self.image_window = ImageWindow(first_image)  # Replace with your image path
        self.image_window.show()

    def load_dark_tl(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select TL Dark", "", "*.npy")
        if path:
            self.dark_tl = np.load(path)

    def load_dark_cb(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CB Dark", "", "*.npy")
        if path:
            self.dark_cb = np.load(path)

    def capture_manual_image(self):
        self.update_status("Capturing images...", True)
        
        name = f"image_{self.image_counter}"
        tl_success, self.cam_tl = si.take_and_save_thorlabs_image(name, self.dark_tl, self.cam_tl)
        
        if tl_success:
            si.take_and_save_cubert_image(name, self.dark_cb, self.acq_ctx, self.proc_ctx)
            self.last_tl_path = os.path.join(si.thorlabs_image_folder, f"{name}_thorlabs.tif")
            self.last_cb_path = os.path.join(si.cubert_image_folder, f"{name}_cubert.tif")
            self.update_display(self.last_tl_path, self.tl_label, 0, True)
            self.update_display(self.last_cb_path, self.cb_label, 0, False)
            self.image_counter += 1
            self.update_status("Image capture complete", False)
        else:
            self.update_status("Thorlabs capture failed", True)

    def capture_auto_image(self):

        if not self.auto_timer_semph.tryAcquire(1, 500):
            print("AUTO CAPTURE IS BUSY. TRY AGAIN NEXT TIME")
            return
        
        self.exposure_cb_input.setValue(int(self.exposure_center_val.text()))

        if self.image_window:
            current_index = self.auto_capture_image_index+int(self.alphebetical_offset_input.text())
            file_name = get_file_at_alphebetical_index(self.dataset_folder, current_index)
            if not file_name:
                self.auto_timer.stop()
                print(f"END OF FILES. IMAGED {self.auto_capture_image_index + 1} FILES")
                self.auto_timer_semph.release(1)
                return
            print(f"ALPHEBETICAL INDEX: {current_index}")
            self.image_window.update_displayed_image(file_name)  
        self.auto_capture_image_index += 1

        MAX_AUTO_EXPOSE_ATTEMPTS = 2
        auto_expose_attempts = 0
        while not self.auto_expose_both():
            auto_expose_attempts += 1
            print(f"Auto Expose Attempt {auto_expose_attempts}")
            if auto_expose_attempts >= MAX_AUTO_EXPOSE_ATTEMPTS:
                print(f"Couldn't find appropriate exposure time! Skipping this file")
                self.auto_timer_semph.release(1)
                return
            
        self.capture_manual_image()

        self.auto_timer_semph.release(1)

    def start_auto_capture(self):
        try:
            interval = int(self.interval_input.text())
            self.auto_capture_image_index = 0
            self.auto_timer.start(interval * 1000)
            self.update_status("Auto capture started", False)
        except ValueError:
            self.update_status("Invalid interval", True)
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid interval in seconds.")

    def stop_auto_capture(self):
        self.auto_timer.stop()
        self.update_status("Auto capture stopped", False)

    def update_display(self, path, label, channel, is_tl):
        if not path or not os.path.exists(path):
            return

        img = tifffile.imread(path)
        if img.ndim == 3:
            img = img[channel]
        img = np.clip(img, 0, None)
        norm = ((img - img.min()) / max(1e-5, img.max() - img.min()) * 255).astype(np.uint8)

        h, w = norm.shape
        qimg = QImage(norm.data, w, h, w, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimg).scaled(500, 500, Qt.KeepAspectRatio)
        label.setPixmap(pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = UnifiedCameraGUI()
    gui.show()
    sys.exit(app.exec_())