import logging
import re
from typing import List

import requests

from amarillo.models.Carpool import Carpool, StopTime
from amarillo.services.config import config
from amarillo.services.secrets import secrets

logger = logging.getLogger(__name__)


class Ride2GoImporter:
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

        carpool = Carpool(
            id=id,
            agency=agency,
            deeplink=dict['deeplink'],
            stops=[Ride2GoImporter._extract_stop(s) for s in dict.get('stops')],
            departureTime=dict.get('departTime'),
            departureDate=dict.get('departDate') if dict.get('departDate') else dict.get('weekdays'),
            lastUpdated=dict.get('lastUpdated'),
        )

        return carpool

    def load_carpools(self) -> List[Carpool]:
        ride2go_query_data = config.ride2go_query_data

        ride2go_url = 'https://ride2go.com/api/v1/trips/export'

        api_key = secrets.ride2go_token

        ride2go_headers = {'Content-type': 'text/plain;charset=UTF-8', 'X-API-Key': f'{api_key}'}

        try:
            result = requests.get(ride2go_url, data=ride2go_query_data, headers=ride2go_headers)
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
