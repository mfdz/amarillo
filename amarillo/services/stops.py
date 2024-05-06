import codecs
import csv
import logging
import re
from contextlib import closing
from io import TextIOWrapper

import geopandas as gpd
import pandas as pd
import requests
from pyproj import Proj, Transformer
from shapely.geometry import LineString, Point
from shapely.ops import transform

from amarillo.models.Carpool import StopTime

from .stop_importer import CsvStopsImporter, GeojsonStopsImporter, GtfsStopsImporter, OverpassStopsImporter

logger = logging.getLogger(__name__)


def is_carpooling_stop(stop_id, name):
    stop_name = name.lower()
    # mfdz: or bbnavi: prefixed stops are custom stops which are explicitly meant to be carpooling stops
    return stop_id.startswith('mfdz:') or stop_id.startswith('bbnavi:') or 'mitfahr' in stop_name or 'p&m' in stop_name


class StopsStore:
    def __init__(self, stop_sources=None, internal_projection='EPSG:32632'):
        self.internal_projection = internal_projection
        self.projection = Transformer.from_crs('EPSG:4326', internal_projection, always_xy=True).transform
        self.stopsDataFrames = []
        self.stop_sources = stop_sources if stop_sources is not None else []

    def load_stop_sources(self):
        """Imports stops from  stop_sources and registers them with
        the distance they are still associated with a trip.
        E.g. bus stops should be registered with a distance of e.g. 30m,
        while larger carpool parkings might be registered with e.g. 500m.

        Subsequent calls of load_stop_sources will reload all stop_sources
        but replace the current stops only if all stops could be loaded successfully.
        """
        stopsDataFrames = []
        error_occured = False

        for stops_source in self.stop_sources:
            try:
                source_url = stops_source.get('url')
                source_type = stops_source.get('type') or (
                    'geojson'
                    if source_url is not None and source_url.startswith('http') and source_url.endswith('json')
                    else 'csv'
                )

                logger.info('Loading stop source %s...', stops_source.get('id', stops_source.get('url')))
                match source_type:
                    case 'geojson':
                        stopsDataFrame = GeojsonStopsImporter().load_stops(source_url)
                    case 'csv':
                        stopsDataFrame = CsvStopsImporter().load_stops(source_url)
                    case 'overpass':
                        stopsDataFrame = OverpassStopsImporter().load_stops(**stops_source)
                    case 'gtfs':
                        stopsDataFrame = GtfsStopsImporter().load_stops(**stops_source)
                    case _:
                        logger.error('Failed to load stops, source type %s not supported', source_type)
                        continue
                stopsDataFrame.to_crs(crs=self.internal_projection, inplace=True)
                stopsDataFrames.append({'distanceInMeter': stops_source['vicinity'], 'stops': stopsDataFrame})
            except Exception:
                error_occured = True
                logger.error('Failed to load stops from %s to StopsStore.', stops_source, exc_info=True)

        if not error_occured:
            self.stopsDataFrames = stopsDataFrames

    def find_additional_stops_around(self, line, stops=None):
        """Returns a GeoDataFrame with all stops in vicinity of the
        given line, sorted by distance from origin of the line.
        Note: for internal projection/distance calculations, the
        lat/lon geometries of line and stops are converted to
        """
        stops_frames = []
        if stops:
            stops_frames.append(self._convert_to_dataframe(stops))
        transformedLine = transform(self.projection, LineString(line.coordinates))
        for stops_to_match in self.stopsDataFrames:
            stops_frames.append(
                self._find_stops_around_transformed(
                    stops_to_match['stops'], transformedLine, stops_to_match['distanceInMeter']
                )
            )
        stops = gpd.GeoDataFrame(pd.concat(stops_frames, ignore_index=True, sort=True))
        if not stops.empty:
            self._sort_by_distance(stops, transformedLine)
        return stops

    def find_closest_stop(self, carpool_stop, max_search_distance):
        transformedCoord = Point(self.projection(carpool_stop.lon, carpool_stop.lat))
        best_dist = max_search_distance + 1
        best_stop = None
        for stops_with_dist in self.stopsDataFrames:
            stops = stops_with_dist['stops']
            s, d = stops.sindex.nearest(
                transformedCoord, return_all=True, return_distance=True, max_distance=max_search_distance
            )
            if len(d) > 0 and d[0] < best_dist:
                best_dist = d[0]
                row = s[1][0]
                best_stop = StopTime(name=stops.at[row, 'stop_name'], lat=stops.at[row, 'y'], lon=stops.at[row, 'x'])

        return best_stop if best_stop else carpool_stop

    def _find_stops_around_transformed(self, stopsDataFrame, transformedLine, distance):
        bufferedLine = transformedLine.buffer(distance)
        sindex = stopsDataFrame.sindex
        possible_matches_index = list(sindex.intersection(bufferedLine.bounds))
        possible_matches = stopsDataFrame.iloc[possible_matches_index]

        return possible_matches[possible_matches.intersects(bufferedLine)]

    def _convert_to_dataframe(self, stops):
        return gpd.GeoDataFrame(
            [[stop.name, stop.lon, stop.lat, stop.id, Point(self.projection(stop.lon, stop.lat))] for stop in stops],
            columns=['stop_name', 'x', 'y', 'id', 'geometry'],
            crs=self.internal_projection,
        )

    def _sort_by_distance(self, stops, transformedLine):
        stops['distance'] = stops.apply(lambda row: transformedLine.project(row['geometry']), axis=1)
        stops.sort_values('distance', inplace=True)
