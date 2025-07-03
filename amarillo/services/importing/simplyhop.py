import logging
import json
from typing import List

from amarillo.models.Carpool import Carpool, StopTime
from amarillo.utils.get import get
from amarillo.services.importing.amarillo import AmarilloImporter

logger = logging.getLogger(__name__)


class SimplyHopImporter(AmarilloImporter):
    
    def _offers_raw(self):
        """
        Requests carpool offers for carpools url.
        The url may be provided as a file:// url to allow
        unit testing.
        """
        if self.carpools_url.startswith("file://"):
            with open(self.carpools_url[7:], "r") as f:
                result = json.load(f)
        else:
            next_url = self.carpools_url
            while next_url is not None:
                response = get(next_url, headers=self.carpools_http_headers, timeout=60)
                result = response.json()
                for offer in result.get('data'):
                    yield offer
                next_url = result.get('link', {}).get('next')
