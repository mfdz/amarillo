import logging
import re
from typing import List

import requests

from amarillo.models.Carpool import Carpool, StopTime
from amarillo.services.config import config
from amarillo.services.secrets import secrets

logger = logging.getLogger(__name__)


class Ride2GoImporter:

    def __init__(self, url, http_headers: dict[str, str] = {}):
        self.carpools_url = str(url)
        self.carpools_http_headers = http_headers

    @staticmethod
    def _extract_stop(stop):
        return StopTime(
            # id="todo",
            name=stop['address'],
            lat=stop['coordinates']['lat'],
            lon=stop['coordinates']['lon'],
        )

    @staticmethod
    def _extract_carpool(dict) -> Carpool:
        (agency, id) = re.findall(r'https?://(.*)\..*/?trip=([0-9]+)', dict['deeplink'])[0]

        lastUpdated = dict.get('lastUpdated')
        carpool = Carpool(
            id=id,
            agency='ride2go',
            deeplink=dict['deeplink'],
            stops=[Ride2GoImporter._extract_stop(s) for s in dict.get('stops')],
            departureTime=dict.get('departTime'),
            departureDate=dict.get('departDate') if dict.get('departDate') else dict.get('weekdays'),
            lastUpdated=lastUpdated +'T00:00:00' if lastUpdated and len(lastUpdated) == 10 else lastUpdated
        )

        return carpool

    def load_carpools(self) -> List[Carpool]:
        ride2go_query_data = config.ride2go_query_data
        try:
            result = requests.get(self.carpools_url, data=ride2go_query_data, headers=self.carpools_http_headers)
            if result.status_code == 200:
                json_results = result.json()
                carpools = [self._extract_carpool(cp) for cp in json_results]

                return carpools
            else:
                logger.error('ride2go request returned with status_code %s', result.status_code)
                json_results = result.json()
                if 'status' in json_results:
                    logger.error('Error was: %s', result.json()['status'])

                raise ValueError('Sync failed with error. See logs')

        except BaseException as e:
            logger.exception('Error on import for agency ride2go')
            raise e
