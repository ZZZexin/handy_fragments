import os

# find file_name_list
def finder(file_type:str):
    current_path = os.path.dirname(__file__)
    load_dir = os.path.join(current_path, r'load_dir')
    out_dir = os.path.join(current_path, r'out_dir')

    files = []
    out_paths = []

    for dirpath, dirnames, filenames in os.walk(load_dir):
        for filename in filenames:
            if filename.lower().endswith(file_type):
                files.append(os.path.join(dirpath, filename))
                out_paths.append(os.path.join(out_dir, filename))

    return files, out_paths