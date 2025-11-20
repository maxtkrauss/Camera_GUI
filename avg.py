from PIL import Image
import numpy as np

image_path = r"F:\Morales\10162025\ratio_exp_2\12mm_ap_4_white.tif"

# Load the TIFF image
image = Image.open(image_path)

# Define crop parameters
top_left_x = 636  # example x-coordinate
top_left_y = 266  # example y-coordinate
square_size = 1004  # example square size

# Crop the image
crop_box = (top_left_x, top_left_y, top_left_x + square_size, top_left_y + square_size)
cropped_image = image.crop(crop_box)

# Convert to NumPy array
image_array = np.array(cropped_image)

# Compute average pixel value
average_pixel = image_array.mean()

print(average_pixel)