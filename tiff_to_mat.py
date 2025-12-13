from sys import argv
import scipy.io
from tifffile import imread
import glob
from pathlib import Path

files = Path(argv[1])

for f in files.iterdir():
    arr = imread(f)
    path = Path(argv[2])/f"{f.name.split('.')[0]}.mat"
    print(f"SAVING: {path}")
    scipy.io.matlab.savemat(str(path), {"image": arr})