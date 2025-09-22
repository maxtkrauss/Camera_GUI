import numpy as np
from skimage import io
import os
# === CONFIGURATION ===
thorlabs_dir = r"F:\Morales\Training HSI System for Biological Samples\m2caiseg-training\session_1_09042025\thorlabs\dark_sub"
cubert_dir = r"F:\Morales\Training HSI System for Biological Samples\m2caiseg-training\session_1_09042025\cubert\dark_sub"
output_dir = r"F:\Morales\Training HSI System for Biological Samples\m2caiseg-training\session_1_09042025\processed"
# Crop settings (x, y center and box size)
# TL CORNERS
# 887,191 | 2333,1160
# CB CORNERS
# 43,40 | 363,222
crop_settings = {
    'thorlabs': {'pos': (1610, 676), 'size': 960},
    'cubert': {'pos': (203, 131), 'size': 180}
}
# === FUNCTION DEFINITIONS ===
def crop_and_mirror(img, pos, box_size):
    if img.ndim != 3:
        raise ValueError("Image must be 3D (bands, height, width)")
        
    z, y, x = img.shape
    cx, cy = pos
    half = box_size // 2
    x_min, x_max = max(0, cx - half), min(x, cx + half)
    y_min, y_max = max(0, cy - half), min(y, cy + half)
    
    cropped = img[:, y_min:y_max, x_min:x_max]
    mirrored = np.flip(cropped, axis=1)  # Flip in Y-direction
    
    return cropped, mirrored
def process_folder(folder_path, tag):
    processed = []
    pos = crop_settings[tag]['pos']
    size = crop_settings[tag]['size']
    # Create tag-specific output subdirectory
    tag_output_dir = os.path.join(output_dir, tag)
    os.makedirs(tag_output_dir, exist_ok=True)
    
    for fname in sorted(os.listdir(folder_path)):
        if fname.endswith(".tif"):
            img_path = os.path.join(folder_path, fname)
            img = io.imread(img_path)
            cropped, mirrored = crop_and_mirror(img, pos, size)
            base = os.path.splitext(fname)[0]
            cropped_path = os.path.join(tag_output_dir, f"{base}_{tag}_cropped.tif")
            mirrored_path = os.path.join(tag_output_dir, f"{base}_{tag}.tif")
            # io.imsave(cropped_path, cropped.astype(np.uint16))
            io.imsave(mirrored_path, mirrored.astype(np.uint16))
            # print(f"Saved: {cropped_path}")
            print(f"Saved: {mirrored_path}")
            processed.append((cropped, mirrored))
    
    return processed
# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("Processing Thorlabs images...")
    thorlabs_processed = process_folder(thorlabs_dir, 'thorlabs')
    print("\nProcessing Cubert images...")
    cubert_processed = process_folder(cubert_dir, 'cubert')
    print("\nAll images processed and saved.")
