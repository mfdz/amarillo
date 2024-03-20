import io
import zipfile
from pathlib import Path

import requests

from .base import CsvStopsImporter


class GtfsStopsImporter(CsvStopsImporter):
    def load_stops(self, id, url, timeout=15, **kwargs):
        if url.startswith('http'):
            # TODO: only reload if file is older than x
            gtfs_file = Path(f'data/{id}.gtfs.zip')
            with requests.get(url, timeout=timeout) as response:
                if response.ok:
                    self._store_response(gtfs_file, response)
        else:
            gtfs_file = url

        with zipfile.ZipFile(gtfs_file) as gtfs:
            with gtfs.open('stops.txt', 'r') as stops_file:
                return self._load_stops_from_csv_source(io.TextIOWrapper(stops_file, 'utf-8-sig'))

    def _store_response(self, filename, response):
        with filename.open('wb') as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
