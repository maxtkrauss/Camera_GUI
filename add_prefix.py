#   GENERATED WITH COPILOT
#
#   === History ===
#   Prompt 1: write a python script which appends a prefix to all files in a list of dirs

import os
from sys import argv

def add_prefix_to_files(directories, prefix):
    """
    Append a prefix to all files in the given list of directories.

    Parameters:
    - directories: list of directory paths
    - prefix: string to prepend to each filename
    """
    for directory in directories:
        if not os.path.isdir(directory):
            print(f"Skipping {directory}: not a valid directory")
            continue

        for filename in os.listdir(directory):
            old_path = os.path.join(directory, filename)

            # Skip subdirectories
            if os.path.isdir(old_path):
                continue

            new_filename = prefix + filename
            new_path = os.path.join(directory, new_filename)

            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {filename} -> {new_filename}")
            except Exception as e:
                print(f"Error renaming {filename}: {e}")

# Example usage:
if __name__ == "__main__":
    dirs = argv[2:]
    add_prefix_to_files(dirs, argv[1])
