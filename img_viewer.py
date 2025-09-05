import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import tifffile as tiff
from matplotlib.colors import Normalize
import os
class ImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Image Viewer")
        self.hsi_images = []  # Hyperspectral images (106, x, y)
        self.grey_images = []  # Greyscale diffractograms (5, x, y)
        self.current_hsi_channel = 0
        self.current_grey_channel = 0
        # Create control frame
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        # Create buttons frame
        self.button_frame = tk.Frame(self.control_frame)
        self.button_frame.pack(fill="x", pady=5)
        # Add load buttons for different image types
        self.load_hsi_button = tk.Button(self.button_frame, text="Load HSI Images",
                                        command=lambda: self.load_images(image_type="hsi"))
        self.load_hsi_button.pack(side=tk.LEFT, padx=5)
        self.load_grey_button = tk.Button(self.button_frame, text="Load Grey Images",
                                         command=lambda: self.load_images(image_type="grey"))
        self.load_grey_button.pack(side=tk.LEFT, padx=5)
        self.clear_button = tk.Button(self.button_frame, text="Clear All Images",
                                     command=self.clear_images)
        self.clear_button.pack(side=tk.RIGHT, padx=5)
        self.snr_button = tk.Button(self.button_frame, text="Check SNR", command=self.compute_snr)
        self.snr_button.pack(side=tk.RIGHT, padx=5)
        # Frame for HSI controls
        self.hsi_frame = tk.LabelFrame(self.control_frame, text="Hyperspectral Image Controls")
        self.hsi_frame.pack(fill="x", padx=10, pady=5)
        self.hsi_slider = tk.Scale(self.hsi_frame, from_=0, to=105, orient=tk.HORIZONTAL,
                                  label="HSI Channel", command=self.update_hsi_channel)
        self.hsi_slider.pack(fill="x", padx=10, pady=5)
        # Frame for Greyscale controls
        self.grey_frame = tk.LabelFrame(self.control_frame, text="Greyscale Image Controls")
        self.grey_frame.pack(fill="x", padx=10, pady=5)
        self.grey_slider = tk.Scale(self.grey_frame, from_=0, to=4, orient=tk.HORIZONTAL,
                                   label="Greyscale Channel", command=self.update_grey_channel)
        self.grey_slider.pack(fill="x", padx=10, pady=5)
        # Create a frame for the matplotlib figure
        self.figure_frame = tk.Frame(root)
        self.figure_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Create initial figure
        self.fig = plt.Figure(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.figure_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        # Status label
        self.status_label = tk.Label(root, text="Ready to load images", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    def compute_snr(self):
        results = []
        # Compute SNR for HSI images
        for filename, img in self.hsi_images:
            band = img[self.current_hsi_channel]
            mean_val = np.mean(band)
            std_val = np.std(band)
            snr = mean_val / std_val if std_val > 0 else 0
            results.append(f"HSI: {filename} (Ch {self.current_hsi_channel}) - SNR: {snr:.2f}")
        # Compute SNR for Grey images
        for filename, img in self.grey_images:
            band = img[self.current_grey_channel]
            mean_val = np.mean(band)
            std_val = np.std(band)
            snr = mean_val / std_val if std_val > 0 else 0
            results.append(f"Grey: {filename} (Ch {self.current_grey_channel}) - SNR: {snr:.2f}")
        # Display SNRs in a new window
        if results:
            snr_window = tk.Toplevel(self.root)
            snr_window.title("SNR Results")
            text_box = tk.Text(snr_window, wrap=tk.WORD)
            text_box.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            text_box.insert(tk.END, "\n".join(results))
            text_box.config(state=tk.DISABLED)
        else:
            self.status_label.config(text="No images loaded to compute SNR.")
    def load_images(self, image_type="all"):
        file_paths = filedialog.askopenfilenames(
            title=f"Select {'HSI' if image_type == 'hsi' else 'Greyscale'} Images",
            filetypes=[("TIFF files", "*.tif")]
        )
        if not file_paths:
            return
        # We don't clear previous images, we add to them
        loaded_hsi = 0
        loaded_grey = 0
        skipped = 0
        for fp in file_paths:
            try:
                img = tiff.imread(fp)
                filename = os.path.basename(fp)
                # Identify image type based on first dimension
                if len(img.shape) == 3:  # Only process 3D images
                    if img.shape[0] == 64 or img.shape[0] == 106 and (image_type in ["all", "hsi"]):
                        self.hsi_images.append((filename, img))
                        loaded_hsi += 1
                    elif img.shape[0] == 5 and (image_type in ["all", "grey"]):
                        self.grey_images.append((filename, img))
                        loaded_grey += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
            except Exception as e:
                self.status_label.config(text=f"Error loading {fp}: {str(e)}")
                skipped += 1
        # Enable/disable sliders based on available images
        if self.hsi_images:
            self.hsi_slider.config(state=tk.NORMAL)
        else:
            self.hsi_slider.config(state=tk.DISABLED)
        if self.grey_images:
            self.grey_slider.config(state=tk.NORMAL)
        else:
            self.grey_slider.config(state=tk.DISABLED)
        # Update status
        self.status_label.config(
            text=f"Added {loaded_hsi} HSI and {loaded_grey} Grey images. " +
                 f"Total: {len(self.hsi_images)} HSI, {len(self.grey_images)} Grey. " +
                 f"Skipped {skipped} incompatible files."
        )
        # Update display
        self.update_display()
    def clear_images(self):
        self.hsi_images = []
        self.grey_images = []
        self.hsi_slider.config(state=tk.DISABLED)
        self.grey_slider.config(state=tk.DISABLED)
        self.fig.clear()
        self.canvas.draw()
        self.status_label.config(text="All images cleared")
    def update_hsi_channel(self, val):
        self.current_hsi_channel = int(val)
        self.update_display()
    def update_grey_channel(self, val):
        self.current_grey_channel = int(val)
        self.update_display()
    def update_display(self):
        num_hsi = len(self.hsi_images)
        num_grey = len(self.grey_images)
        total_images = num_hsi + num_grey
        if not total_images:
            self.fig.clear()
            self.canvas.draw()
            return
        # Clear the figure
        self.fig.clear()
        # Determine layout
        cols = min(3, total_images)
        rows = (total_images + cols - 1) // cols
        # Plot all HSI images with current HSI channel
        for i, (filename, img) in enumerate(self.hsi_images):
            ax = self.fig.add_subplot(rows, cols, i + 1)
            img_display = img[self.current_hsi_channel]
            # Normalize to improve visibility
            norm = Normalize(vmin=np.min(img_display), vmax=np.max(img_display))
            im = ax.imshow(img_display, cmap='viridis', norm=norm)
            ax.set_title(f"{filename}\nHSI Ch: {self.current_hsi_channel}", fontsize=9)
            ax.axis("off")
            # Add colorbar
            cbar = self.fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label("Intensity", fontsize=8)
            cbar.ax.tick_params(labelsize=7)
        # Plot all Greyscale images with current Grey channel
        for i, (filename, img) in enumerate(self.grey_images):
            ax = self.fig.add_subplot(rows, cols, i + num_hsi + 1)
            img_display = img[self.current_grey_channel]
            # Normalize to improve visibility
            norm = Normalize(vmin=np.min(img_display), vmax=np.max(img_display))
            im = ax.imshow(img_display, cmap='gray', norm=norm)
            ax.set_title(f"{filename}\nGrey Ch: {self.current_grey_channel}", fontsize=9)
            ax.axis("off")
            # Add colorbar
            cbar = self.fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label("Intensity", fontsize=8)
            cbar.ax.tick_params(labelsize=7)
        self.fig.tight_layout()
        self.canvas.draw()  # Update the canvas to display the new figure
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x800")  # Set initial window size
    viewer = ImageViewer(root)
    root.mainloop()