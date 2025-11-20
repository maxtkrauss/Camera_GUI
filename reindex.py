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
map_file = 'map_train.json'
basedir = r"F:\Morales\exp3 - Youtube Dataset with 3rd Cam Setup\10162025\stretched"

cubert_dir = Path(basedir) / 'cubert'
thorlabs_dir = Path(basedir) / 'thorlabs'
# generate_reindex_file (cubert_dir, ignorelist, map_file)

apply_reindexing(cubert_dir, ignorelist, map_file, "image_#_cubert")
apply_reindexing(thorlabs_dir, ignorelist, map_file, "image_#_thorlabs")