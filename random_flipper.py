import os
import random
from PIL import Image

def apply_random_flips(directory_path, h_flip_prob=0.5, v_flip_prob=0.5):
    # Ensure the directory exists
    if not os.path.isdir(directory_path):
        print("Invalid directory path.")
        return

    # Create output directory
    output_dir = os.path.join(directory_path, "transformed_images")
    os.makedirs(output_dir, exist_ok=True)

    # Process each image in the directory
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        # Skip directories and non-image files
        if not os.path.isfile(file_path) or not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            continue

        # Open the image
        with Image.open(file_path) as img:
            transformed_img = img.copy()

            # Apply horizontal flip with given probability
            if random.random() < h_flip_prob:
                transformed_img = transformed_img.transpose(Image.FLIP_LEFT_RIGHT)

            # Apply vertical flip with given probability
            if random.random() < v_flip_prob:
                transformed_img = transformed_img.transpose(Image.FLIP_TOP_BOTTOM)

            # Save the transformed image
            transformed_img.save(os.path.join(output_dir, filename))

    print(f"Transformations completed. Transformed images are saved in: {output_dir}")
