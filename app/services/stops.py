import csv
import geopandas as gpd
import pandas as pd
from contextlib import closing
from shapely.geometry import Point
from shapely.ops import transform
from pyproj import Proj, Transformer
import re
import requests
from io import TextIOWrapper
import codecs
import logging

logger = logging.getLogger(__name__)

class StopsStore():
    
    def __init__(self, internal_projection = "EPSG:32632"):
        self.projection = Transformer.from_crs("EPSG:4326", internal_projection, always_xy=True).transform
        self.stopsDataFrames = []
    
    def register_stops(self, source : str, distance : int = 500):
        """Imports stops from given source and registers them with
        the distance they are still associated with a trip.
        E.g. bus stops should be registered with a distance of e.g. 30m,
        while larger carpool parkings might be registered with e.g. 500m
        """
        logger.info("Load stops from %s", source)
        if source.startswith('http'):
            with requests.get(source) as csv_source:
                stopsDataFrame = self._load_stops(codecs.iterdecode(csv_source.iter_lines(), 'utf-8'))
        else:
            with open(source, encoding='utf-8') as csv_source:
                stopsDataFrame = self._load_stops(csv_source)
            
        self.stopsDataFrames.append({'distanceInMeter': distance,
            'stops': stopsDataFrame})

    def find_additional_stops_around(self, line, stops = None):
        """Returns a GeoDataFrame with all stops in vicinity of the
        given line, sorted by distance from origin of the line.
        Note: for internal projection/distance calculations, the
        lat/lon geometries of line and stops are converted to 
        """
        stops_frames = []
        if stops:
            stops_frames.append(self._convert_to_dataframe(stops)) 
        transformedLine = transform(self.projection, line)
        for stops_to_match in self.stopsDataFrames:
            stops_frames.append(self._find_stops_around_transformed(stops_to_match['stops'], transformedLine, stops_to_match['distanceInMeter']))
        stops = gpd.GeoDataFrame( pd.concat(stops_frames, ignore_index=True, sort=True)) 
        if not stops.empty:
            self._sort_by_distance(stops, transformedLine)
        return stops

    def _normalize_stop_name(self, stop_name):
        default_name = 'P+R-Parkplatz'
        if stop_name in ('', 'Park&Ride'):
            return default_name
        normalized_stop_name = re.sub(r"P(ark)?\s?[\+&]\s?R(ail|ide)?",'P+R', stop_name)
        
        return normalized_stop_name

    def _load_stops(self, csv_source):
        id = []
        lat = []
        lon = []
        stop_name = []
        reader = csv.DictReader(csv_source, delimiter=';')
        columns = ['stop_id', 'stop_lat', 'stop_lon', 'stop_name']
        lists = [id, lat, lon, stop_name]
        for row in reader:
            for col, lst in zip(columns, lists):
                if col == "stop_lat" or col == "stop_lon":
                    lst.append(float(row[col].replace(",",".")))
                elif col == "stop_name":
                    row_stop_name = self._normalize_stop_name(row[col])
                    lst.append(row_stop_name)
                else:
                    lst.append(row[col])

        stopsDataFrame = gpd.GeoDataFrame(data={'x':lon, 'y':lat, 'stop_name':stop_name, 'id':id})  
        
        stopsDataFrame['geometry'] = stopsDataFrame.apply(lambda row: Point(self.projection(row['x'], row['y'])), axis=1)        
    
        return stopsDataFrame

    def _find_stops_around_transformed(self, stopsDataFrame, transformedLine, distance):
        bufferedLine = transformedLine.buffer(distance)
        sindex = stopsDataFrame.sindex
        possible_matches_index = list(sindex.intersection(bufferedLine.bounds))
        possible_matches = stopsDataFrame.iloc[possible_matches_index]
        exact_matches = possible_matches[possible_matches.intersects(bufferedLine)]
        
        return exact_matches
    
    def _convert_to_dataframe(self, stops):
        return gpd.GeoDataFrame([[stop.name, stop.lon, stop.lat,
            stop.id, Point(self.projection(stop.lon, stop.lat))] for stop in stops], columns = ['stop_name','x','y','id','geometry'])
         
    def _sort_by_distance(self, stops, transformedLine):
        stops['distance']=stops.apply(lambda row: transformedLine.project(row['geometry']), axis=1)
        stops.sort_values('distance', inplace=True)
