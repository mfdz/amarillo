import os

def assert_folder_exists(foldername):
    if not os.path.isdir(foldername):
        os.makedirs(foldername)