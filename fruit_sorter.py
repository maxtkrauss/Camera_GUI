import os
import shutil
import re

# Define paths
fruit_cubert_dir = r"C:\Users\menon\Documents\objects_4-16\fruit\processed\cubert"
fruit_thorlabs_dir = r"C:\Users\menon\Documents\objects_4-16\fruit\processed\thorlabs"
red_cubert_dir = r"C:\Users\menon\Documents\objects_4-16\red_fruit\processed\cubert"
red_thorlabs_dir = r"C:\Users\menon\Documents\objects_4-16\red_fruit\processed\thorlabs"

# Get the highest image index from fruit
existing_files = os.listdir(fruit_cubert_dir)
existing_indices = [
    int(re.search(r"image_(\d+)_cubert_cubert\.tif", f).group(1))
    for f in existing_files if "image_" in f
]
start_index = max(existing_indices) + 1 if existing_indices else 0

# Get sorted red fruit cubert and thorlabs files
red_cubert_files = sorted([
    f for f in os.listdir(red_cubert_dir) if f.endswith("_cubert_cubert.tif")
])
red_thorlabs_files = sorted([
    f for f in os.listdir(red_thorlabs_dir) if f.endswith("_thorlabs_thorlabs.tif")
])

# Sanity check: they must be paired and of the same length
assert len(red_cubert_files) == len(red_thorlabs_files), "Mismatch in red_fruit pair count."

# Rename and move files
for i, (cubert_file, thorlabs_file) in enumerate(zip(red_cubert_files, red_thorlabs_files)):
    new_index = start_index + i
    new_cubert_name = f"image_{new_index}_cubert_cubert.tif"
    new_thorlabs_name = f"image_{new_index}_thorlabs_thorlabs.tif"

    shutil.copy2(os.path.join(red_cubert_dir, cubert_file), os.path.join(fruit_cubert_dir, new_cubert_name))
    shutil.copy2(os.path.join(red_thorlabs_dir, thorlabs_file), os.path.join(fruit_thorlabs_dir, new_thorlabs_name))

print("Red fruit images successfully renamed and moved.")
