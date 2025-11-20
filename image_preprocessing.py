import numpy as np
from skimage import io
import os
from argparse import ArgumentParser

# === FUNCTION DEFINITIONS ===
def crop_and_mirror(img, pos, box_size):
    if img.ndim != 3:
        raise ValueError("Image must be 3D (bands, height, width)")
        
    z, y, x = img.shape
    cx, cy = pos
    x_min, x_max = max(0, cx), min(x, cx + box_size)
    y_min, y_max = max(0, cy), min(y, cy + box_size)
    
    cropped = img[:, y_min:y_max, x_min:x_max]
    # mirrored = np.flip(cropped, axis=1)  # Flip in Y-direction
    
    return cropped#, mirrored

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
            cropped = crop_and_mirror(img, pos, size)
            base = os.path.splitext(fname)[0]
            cropped_path = os.path.join(tag_output_dir, f"{base}_{tag}_cropped.tif")
            # mirrored_path = os.path.join(tag_output_dir, f"{base}_{tag}.tif")
            # io.imsave(cropped_path, cropped.astype(np.uint16))
            io.imsave(cropped_path, cropped.astype(np.uint16))
            # print(f"Saved: {cropped_path}")
            print(f"Saved: {cropped_path}")
            processed.append((cropped))
    
    return processed

def set_globals (args):
    '''
    This function is very bad practice! Don't replicate.
    '''
    global base_dir
    base_dir = args.input_base
    global thorlabs_dir
    thorlabs_dir = os.path.join(base_dir, r"thorlabs")
    global cubert_dir
    cubert_dir = os.path.join(base_dir, r"cubert")
    global output_dir
    output_dir = args.output_base
    # Crop settings (x, y center and box size)
    # TL CORNERS
    # 887,191 | 2333,1160
    # CB CORNERS
    # 43,40 | 363,222
    global crop_settings
    crop_settings = {
        'thorlabs': {'pos': (args.x_thorlabs, args.y_thorlabs), 'size': args.size_thorlabs},
        'cubert': {'pos': (args.x_cubert, args.y_cubert), 'size': args.size_cubert}
    }

# === MAIN EXECUTION ===
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input_base")
    parser.add_argument("-o", "--output_base")
    parser.add_argument("-xt", "--x_thorlabs", type=int)
    parser.add_argument("-yt", "--y_thorlabs", type=int)
    parser.add_argument("-st", "--size_thorlabs", type=int)
    parser.add_argument("-xc", "--x_cubert", type=int)
    parser.add_argument("-yc", "--y_cubert", type=int)
    parser.add_argument("-sc", "--size_cubert", type=int)

    args = parser.parse_args()
    set_globals(args)

    print("Processing Thorlabs images...")
    thorlabs_processed = process_folder(thorlabs_dir, 'thorlabs')
    print("\nProcessing Cubert images...")
    cubert_processed = process_folder(cubert_dir, 'cubert')
    print("\nAll images processed and saved.")
