import os
import numpy as np
import tifffile as tiff
def load_images_from_folder(folder):
    """Load all .tif images from a folder."""
    images = []
    for filename in os.listdir(folder):
        if filename.endswith(".tif"):
            filepath = os.path.join(folder, filename)
            images.append(tiff.imread(filepath))
    return np.array(images)
def save_image(image, filepath):
    """Save a single image to a .tif file."""
    tiff.imwrite(filepath, image.astype(np.float32))
def create_average_dark_frame(dark_frame_folder):
    """Create an average dark frame from all dark frames in a folder."""
    dark_frames = load_images_from_folder(dark_frame_folder)
    return np.mean(dark_frames, axis=0)
def subtract_dark_frame_and_save(input_folder, output_folder, dark_frame):
    """Subtract the dark frame from each image in the input folder and save to the output folder."""
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if filename.endswith(".tif"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            image = tiff.imread(input_path)
            corrected_image = image - dark_frame
            # Clip negative values to zero
            corrected_image = np.clip(corrected_image, 0, None)
            save_image(corrected_image, output_path)
            print(f"Saved: {output_path}")
def process_camera_data(dark_frame_folder, input_folder, output_folder):
    """Process data for a single camera."""
    print(f"Processing data for folder: {input_folder}")
    dark_frame = create_average_dark_frame(dark_frame_folder)
    subtract_dark_frame_and_save(input_folder, output_folder, dark_frame)

if __name__ == "__main__":
    input_base_folder = r"F:\Morales\exp3 - Youtube Dataset with 3rd Cam Setup\10162025\captures"
    dark_frame_base_folder = r"F:\Morales\exp3 - Youtube Dataset with 3rd Cam Setup\10162025\darkframes"
    # Define paths for Thorlabs camera
    thorlabs_dark_frame_folder = os.path.join(dark_frame_base_folder, "thorlabs")
    thorlabs_input_folder = os.path.join(input_base_folder, "thorlabs")
    thorlabs_output_folder = os.path.join(thorlabs_input_folder, "dark_sub")

    # Define paths for Cubert camera
    cubert_dark_frame_folder = os.path.join(dark_frame_base_folder, "cubert")
    cubert_input_folder = os.path.join(input_base_folder, "cubert")
    cubert_output_folder = os.path.join(cubert_input_folder, "dark_sub")

    # Process data for both cameras
    process_camera_data(thorlabs_dark_frame_folder, thorlabs_input_folder, thorlabs_output_folder)
    process_camera_data(cubert_dark_frame_folder, cubert_input_folder, cubert_output_folder)
    print("Dark frame subtraction completed.")