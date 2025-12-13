#   GENERATED WITH COPILOT
#
#   === History ===
# Prompt 1: write a python script which sorts a directory alphebetically and then copies the files at particular indices to a given dir

import os
import shutil

def copy_selected_files(src_dir, dest_dir, indices):
    """
    Sorts files in src_dir alphabetically and copies files at given indices to dest_dir.

    :param src_dir: Source directory containing files
    :param dest_dir: Destination directory where selected files will be copied
    :param indices: List of integer indices of files to copy (0-based)
    """
    # Ensure destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    # Get sorted list of files (ignore subdirectories)
    files = sorted([f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))])

    # Copy files at specified indices
    for idx in indices:
        if 0 <= idx < len(files):
            src_path = os.path.join(src_dir, files[idx])
            dest_path = os.path.join(dest_dir, files[idx])
            shutil.copy2(src_path, dest_path)
            print(f"Copied: {files[idx]}")
        else:
            print(f"Index {idx} out of range. Skipping.")

# Example usage:
if __name__ == "__main__":
    source_directory = r"/home/matthew-morales/Documents/MeatyDB Results 12-04-2025/images"
    destination_directory = "./selected/re"
    offset = 174
    selected_indices = [offset+i for i in [75, 93]]  # Example: copy 1st, 3rd, and 6th files
    copy_selected_files(source_directory, destination_directory, selected_indices)
