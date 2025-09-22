import tifffile
import numpy as np
from skimage.transform import resize
import os

def resize_tiff(input_path, target_shape, output_path=None):
    """
    Resize a multi-dimensional TIFF file to the given shape.

    Parameters:
    - input_path (str): Path to the input TIFF file.
    - target_shape (tuple): Desired shape (e.g., (z, y, x) or (y, x) depending on the image).
    - output_path (str, optional): Path to save the resized TIFF. If None, overwrites the input file.
    """
    # Read the TIFF file
    with tifffile.TiffFile(input_path) as tif:
        image = tif.asarray()

    # Resize the image
    resized_image = resize(image, target_shape, preserve_range=True, anti_aliasing=True).astype(image.dtype)

    # Determine output path
    save_path = output_path if output_path else input_path

    # Save the resized image
    tifffile.imwrite(save_path, resized_image)

    print(f"Resized image saved to: {save_path}")

def find_tiff_files(directory):
    """
    Recursively search for TIFF files in a directory and its subdirectories.

    Parameters:
    - directory (str): The root directory to start the search.

    Returns:
    - List[str]: A list of absolute paths to TIFF files.
    """
    tiff_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.tif', '.tiff')):
                full_path = os.path.abspath(os.path.join(root, file))
                tiff_files.append(full_path)
    return tiff_files


for file in find_tiff_files('./test/thorlabs'):
    resize_tiff(file, (5, 660, 660))