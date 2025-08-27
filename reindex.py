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
        f.write(json.dumps(mappings))
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
                print(f"RENAMING {f.name} TO {new_name}")


ignorelist = ['cubert', 'thorlabs']
map_file = 'map.json'
source_dir = './test/cubert'
target_dir = './test/thorlabs'

generate_reindex_file (source_dir, ignorelist, map_file)
apply_reindexing(source_dir, ignorelist, map_file, template="image_#_thorlabs")
apply_reindexing(target_dir, ignorelist, map_file, template="image_#_cubert")
