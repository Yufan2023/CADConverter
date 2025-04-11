import os

def get_file_extension(fpath):
    return os.path.splitext(fpath)[1].lower()

def basename_without_ext(fpath):
    return os.path.splitext(os.path.basename(fpath))[0]
