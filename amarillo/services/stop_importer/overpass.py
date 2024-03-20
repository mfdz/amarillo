import csv
import io
import logging

import requests

from .base import BaseStopsImporter

logger = logging.getLogger(__name__)


class OverpassStopsImporter(BaseStopsImporter):
    def load_stops(self, area_selector, timeout=15, **kwargs):
        query = f'''
            [out:csv(::"type", ::"id", ::"lat", ::"lon", name,parking,park_ride,operator,access,lit,fee,capacity,"capacity:disabled",supervised,surface,covered,maxstay,opening_hours)][timeout:60];
            area{area_selector}->.a;
            nwr(area.a)[park_ride][park_ride!=no][access!=customers];
            out center;
            '''

        response = requests.post('https://overpass-api.de/api/interpreter', data=query, timeout=timeout)
        if not response.ok:
            logger.error(f'Error retrieving stops from overpass: {response.text}')

        return self._parse_overpass_csv_response(response.text.splitlines())

    def _parse_overpass_csv_response(self, csv_source):
        id = []
        lat = []
        lon = []
        stop_name = []
        reader = csv.DictReader(csv_source, delimiter='\t')
        for row in reader:
            id.append(f'osm:{row["@type"][0]}{row["@id"]}')
            lat.append(float(row['@lat']))
            lon.append(float(row['@lon']))
            stop_name.append(self._normalize_stop_name(row['name']))

        return self._as_dataframe(id, lat, lon, stop_name)
