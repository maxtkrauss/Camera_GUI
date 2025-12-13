# This script is used to help generate the "Data Cube" Illustrations

from sys import argv
import matplotlib.pyplot as plt
from matplotlib.axis import Axis
from tifffile import imread, imwrite
from pathlib import Path
from PIL import Image
path = Path(argv[1])

im_data = imread(str(path))
print(im_data.shape)
for wi in range(im_data.shape[0]//2):
    plt.imsave(f'./split-gen/{wi}.png', im_data[wi], cmap="viridis")