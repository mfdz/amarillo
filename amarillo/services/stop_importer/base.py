import codecs
import csv
import logging
import re

import geopandas as gpd
import requests

logger = logging.getLogger(__name__)


class BaseStopsImporter:
    def _normalize_stop_name(self, stop_name):
        # if the name is empty, we set P+R as a fall back. However, it should be named at the source
        default_name = 'P+R'
        if stop_name in ('', 'Park&Ride'):
            return default_name
        return re.sub(r'P(ark)?\s?[\+&]\s?R(ail|ide)?', 'P+R', stop_name)

    def _as_dataframe(self, id, lat, lon, stop_name):
        df = gpd.GeoDataFrame(data={'x': lon, 'y': lat, 'stop_name': stop_name, 'id': id})
        return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.x, df.y, crs='EPSG:4326'))


class CsvStopsImporter(BaseStopsImporter):
    DEFAULT_COLUMN_MAPPING = {
        'stop_id': 'stop_id',
        'stop_lat': 'stop_lat',
        'stop_lon': 'stop_lon',
        'stop_name': 'stop_name',
    }

    def load_stops(self, source, timeout=15):
        if source.startswith('http'):
            with requests.get(source, timeout=timeout) as csv_source:
                return self._load_stops_from_csv_source(
                    codecs.iterdecode(csv_source.iter_lines(), 'utf-8'), delimiter=';'
                )
        else:
            with open(source, encoding='utf-8') as csv_source:
                return self._load_stops_from_csv_source(csv_source, delimiter=';')

    def _load_stops_from_csv_source(self, csv_source, delimiter: str = ',', column_mapping=None):
        if column_mapping is None:
            column_mapping = self.DEFAULT_COLUMN_MAPPING
        id = []
        lat = []
        lon = []
        stop_name = []
        reader = csv.DictReader(csv_source, delimiter=delimiter)
        for row in reader:
            id.append(row[column_mapping['stop_id']])
            lat.append(float(row[column_mapping['stop_lat']].replace(',', '.')))
            lon.append(float(row[column_mapping['stop_lon']].replace(',', '.')))
            stop_name.append(self._normalize_stop_name(row[column_mapping['stop_name']]))

        return self._as_dataframe(id, lat, lon, stop_name)


class GeojsonStopsImporter(BaseStopsImporter):
    def load_stops(self, source, timeout=15):
        with requests.get(source, timeout=timeout) as json_source:
            geojson_source = json_source.json()
            id = []
            lat = []
            lon = []
            stop_name = []
            for row in geojson_source['features']:
                coord = row['geometry']['coordinates']
                if not coord or not row['properties'].get('name'):
                    logger.error('Stop feature {} has null coord or name'.format(row['id']))
                    continue

                id.append(row['id'])
                lon.append(coord[0])
                lat.append(coord[1])
                stop_name.append(self._normalize_stop_name(row['properties']['name']))

            return self._as_dataframe(id, lat, lon, stop_name)
