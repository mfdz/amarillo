import os
import re

def assert_folder_exists(foldername):
    if not os.path.isdir(foldername):
        os.makedirs(foldername)


def agency_carpool_ids_from_filename(carpool_filename):
    """ 
    Returns agency_id, carpool_id from a carpool filename.
    It is assumed, that carpool_filename matches the regex
    /([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+).json$
    """  
    m = re.search(r'\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_-]+)\.json$', carpool_filename)
    if m:
        return m[1], m[2]
    else:
        return None, None