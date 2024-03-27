import os
import re
import shutil
from pathlib import Path
import logging

from datetime import datetime, date, timedelta
from pyproj import Geod

logger = logging.getLogger(__name__)
#logging.conf may not exist yet, so we need to configure the logger to show infos
logging.basicConfig(level=logging.INFO) 

def assert_folder_exists(foldername):
    if not os.path.isdir(foldername):
        os.makedirs(foldername, exist_ok=True)


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

def is_older_than_days(date_to_check, number_of_days):
    if date_to_check is None:
        return True
    if isinstance(date_to_check, datetime):
        date_to_check = date_to_check.date()
    return date_to_check < date_days_ago(number_of_days)

def yesterday():
    return date_days_ago(1)

def date_days_ago(number_of_days):
    return date.today() - timedelta(days=number_of_days)

def geodesic_distance_in_m(coord1, coord2):
    geod = Geod(ellps="WGS84")
    lons = [coord1[0], coord2[0]]
    lats = [coord1[1], coord2[1]]
    return geod.line_lengths(lons, lats)[0]


def copy_static_files(files_and_dirs_to_copy):
    amarillo_dir = Path(__file__).parents[1]
    source_dir = os.path.join(amarillo_dir, "static")

    destination_dir = os.getcwd()

    for item in files_and_dirs_to_copy:
        source_path = os.path.join(source_dir, item)
        destination_path = os.path.join(destination_dir, item)

        if not os.path.exists(source_path):
            raise FileNotFoundError(source_path)

        if os.path.exists(destination_path):
            # logger.info(f"{item} already exists")
            continue

        if os.path.isfile(source_path):
            shutil.copy2(source_path, destination_path)
            logger.info(f"Copied {item} to {destination_path}")

        if os.path.isdir(source_path):
            shutil.copytree(source_path, destination_path)
            logger.info(f"Copied directory {item} and its contents to {destination_path}")