import tifffile
import numpy as np
import random
from pathlib import Path
from sys import argv

def vertical_flip_tiff(input_path, output_path):
    # Read the TIFF file
    with tifffile.TiffFile(input_path) as tif:
        image_data = tif.asarray()

    # Flip the image vertically along the first spatial axis (usually axis 0)
    flipped_data = np.flip(image_data, axis=1)
    double_flipped_data = np.flip(flipped_data, axis=2)

    # Save the flipped image to a new TIFF file
    tifffile.imwrite(output_path, double_flipped_data)

def batch_flip (input_dir, output_dir, copies=3, seed=31415):
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

    for file in input_path.glob("*.tif"):
        for _ in range(copies):
            vertical_flip_tiff(Path(input_path, file.name), Path(output_path, file.name))

batch_flip(argv[1], argv[2])