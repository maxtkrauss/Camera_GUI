from pathlib import Path
import json
import os

# "/scratch/general/nfs1/u1344001/data/EndoDBV1/training/cubert"
def generate_reindex_file (path, ignorelist=[], outfile='map.json'):
    p = Path(path)
    
    mappings = {}
    index = 0
    
    for f in p.iterdir():
        if not f.is_dir():
            clean_name = f.name
            for word in ignorelist:
                clean_name = clean_name.replace(word, '')
            mappings[clean_name] = index
            index += 1
    
    with open(outfile, 'w') as f:
        f.write(json.dumps(mappings, indent=4))
        print(f"WROTE INDEX FILE TO {outfile}")

def apply_reindexing (path, ignorelist=[], index_file='map.json', template="#"):
    index_path = Path(index_file)
    if not index_path.exists():
        print("INDEX FILE NOT FOUND")
    mappings: dict = json.loads(index_path.read_text())
    
    p = Path(path)
    
    for f in p.iterdir():
        if not f.is_dir():
            clean_name = f.name
            for word in ignorelist:
                clean_name = clean_name.replace(word, '')
            index = mappings.get(clean_name, None)
            if index is not None:
                _, ext = os.path.splitext(f.name)
                new_name = template.replace('#', str(index))+ext
                f.rename(f.parent / new_name)
                print(f"RENAMING {f.name} TO {new_name}")


# generate_reindex_file('./test/cubert', ['cubert', 'thorlabs'])
# apply_reindexing('./test/cubert', ['cubert', 'thorlabs'], 'map.json', template="image_#_cubert")
# apply_reindexing('./test/thorlabs', ['cubert', 'thorlabs'], 'map.json', template="image_#_thorlabs")

ignorelist = ['cubert', 'thorlabs']
map_file_train = 'map_train.json'
map_file_valid = 'map_valid.json'
basedir = '/scratch/general/nfs1/u1344001/data/EndoDBV1/'

source_dir = Path(basedir) / 'training/cubert'
target_dir = Path(basedir) / 'training/thorlabs'
generate_reindex_file (source_dir, ignorelist, map_file_train)
apply_reindexing(source_dir, ignorelist, map_file_train, template="image_#_thorlabs")
apply_reindexing(target_dir, ignorelist, map_file_train, template="image_#_cubert")

source_dir = Path(basedir) / 'validation/cubert'
target_dir = Path(basedir) / 'validation/thorlabs'
generate_reindex_file (source_dir, ignorelist, map_file_valid)
apply_reindexing(source_dir, ignorelist, map_file_valid, template="image_#_thorlabs")
apply_reindexing(target_dir, ignorelist, map_file_valid, template="image_#_cubert")