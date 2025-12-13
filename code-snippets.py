from matplotlib.image import imsave
from tifffile import imread

HSI_FILE_PATH = ""
SAVE_PATH = ""
LAYER_INDEX = 0

arr = imread(HSI_FILE_PATH)
print(arr.shape) # Should be (106, 410, 410) depending on cropping

imsave(SAVE_PATH, arr[LAYER_INDEX])