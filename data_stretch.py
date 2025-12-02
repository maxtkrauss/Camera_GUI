import numpy as np
import tifffile
from skimage.transform import rotate as trotate
from pathlib import Path
import random
from sys import argv
from PIL import Image

def rotate_tiff_image(image_path, angle_degrees, save_path=None):
    """
    Rotates a multi-dimensional TIFF image by a given angle in radians.

    Parameters:
    - image_path (str): Path to the input TIFF image.
    - angle_radians (float): Angle to rotate the image, in radians.
    - save_path (str, optional): Path to save the rotated image. If None, the image is not saved.

    Returns:
    - Rotated image as a numpy array.
    """
    # Load the TIFF image
    image = tifffile.imread(image_path)

    # Rotate based on image dimensions
    if image.ndim == 2:
        # Grayscale image
        rotated_image = trotate(image, angle_degrees, resize=False, preserve_range=True).astype(image.dtype)
    else:
        # Multi-channel or 3D image
        rotated_image = np.stack([
            trotate(image[i], angle_degrees, resize=False, preserve_range=True).astype(image.dtype)
            for i in range(image.shape[0])
        ])

    # Save the rotated image if a path is provided
    if save_path:
        tifffile.imwrite(save_path, rotated_image)

    rotated_image = None

def rotate_png_image(image_path, angle_degrees, save_path=None):
    """
    Rotates a PNG image by a given angle in degrees.

    Parameters:
    - image_path (str): Path to the input PNG image.
    - angle_degrees (float): Angle to rotate the image, in degrees.
    - save_path (str, optional): Path to save the rotated image. If None, the image is not saved.

    Returns:
    - Rotated image as a numpy array.
    """
    # Load the PNG image
    image = Image.open(image_path)
    image_array = np.array(image)

    # Rotate the image
    if image_array.ndim == 2:
        # Grayscale image
        rotated_array = trotate(image_array, angle_degrees, resize=False, preserve_range=True).astype(image_array.dtype)
    else:
        # RGB or RGBA image
        rotated_array = np.stack([
            trotate(image_array[..., channel], angle_degrees, resize=False, preserve_range=True).astype(image_array.dtype)
            for channel in range(image_array.shape[-1])
        ], axis=-1)

    # Save the rotated image if a path is provided
    if save_path:
        rotated_image = Image.fromarray(rotated_array)
        rotated_image.save(save_path)

    rotated_image = None

def get_rotate_func (ext):
    if ext == '.tif':
        return rotate_tiff_image
    elif ext == '.png':
        return rotate_png_image

def batch_rotate_tiff_images(input_dir, output_dir, copies=3, seed=31415, ext='.tif'):
    """
    Rotates all TIFF images in the input directory by a random angle (0–360 degrees)
    and saves them to the output directory.

    Parameters:
    - input_dir (str): Path to the directory containing TIFF images.
    - output_dir (str): Path to the directory where rotated images will be saved.
    """

    random.seed(seed)

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for file in input_path.glob(f"*{ext}"):
        for _ in range(copies):
            random_degrees = int(random.randint(0, 360))
            output_file = output_path.joinpath(f"rot{random_degrees}{file.name}")
            get_rotate_func(ext)(str(file), random_degrees, str(output_file))
            print(f"Rotated {file.name} by {random_degrees} degrees.")

batch_rotate_tiff_images(argv[1], argv[2], int(argv[3]), int(argv[4]), argv[5])