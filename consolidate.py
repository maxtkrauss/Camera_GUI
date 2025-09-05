import os
import sys
import re
import shutil
import json

DEVICES = ["thorlabs", "cubert"]
EXT = 'tif'

def clear_directory(path):
    if os.path.exists(path) and os.path.isdir(path):
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # delete file or symlink
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # delete subdirectory

# Read process dirs
process_dirs = []
with open("directories.txt", 'r') as directoryfile:
    for line in directoryfile.readlines():
        process_dirs.append(line.strip())

# Create path for final images
target_dir = sys.argv[1]
clear_directory(target_dir)
os.makedirs(os.path.join(target_dir, "thorlabs"))
os.makedirs(os.path.join(target_dir, "cubert"))

# Find images in a directory and get a mapping from its original number to its new
def get_number_maps (dirpath, starting_index):
    index = starting_index
    number_maps = {}
    device = DEVICES[0]
    for file in os.listdir(os.path.join(dirpath, device)):
        match = re.search(r"(?<=image_)\d+(?=_thorlabs)", file)
        if match:
            number = int(match.group())
            number_maps[number] = index
            index += 1

    return number_maps

def copy_files (original_dir, final_dir, number_maps, device, dry=False):
    for oldnum, newnum in number_maps.items():
        oldfile = os.path.join(original_dir, device, f"image_{oldnum}_{device}_{device}.{EXT}")
        newfile = os.path.join(final_dir, device, f"image_{newnum}_{device}_{device}.{EXT}")
        print(f"Copying {oldfile} to {newfile}")
        if not dry:
            shutil.copy(oldfile, newfile)
        
    
directory_numbermaps = {}
current_index = 0
for dirpath in process_dirs:
    number_maps = get_number_maps(dirpath, current_index)
    current_index += len(number_maps)
    directory_numbermaps[dirpath] = number_maps
    for device in DEVICES:
        copy_files(dirpath, target_dir, number_maps, device)
                


with open(os.path.join(target_dir, "mappings.json"), "w") as mappings_file:
    mappings_file.write(json.dumps(directory_numbermaps, indent=4))