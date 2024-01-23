import os
import re
from datetime import datetime, date, timedelta
from pyproj import Geod

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