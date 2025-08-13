import logging
import re
from datetime import datetime, timedelta
from typing import List

import requests

from amarillo.models.Carpool import Carpool, StopTime
from amarillo.services.config import config

logger = logging.getLogger(__name__)


class NoiImporter:
    carpools_request_url = 'https://mobility.api.opendatahub.testingmachine.eu/v2/flat,node/CarpoolingTrip/*/latest'

    def __init__(self, agency_id: str, carpools_request_url: str = None, test_mode: bool = False):
        self.agency_id = agency_id.upper()
        self.test_mode = test_mode
        if carpools_request_url is not None:
            self.carpools_request_url = carpools_request_url

    @staticmethod
    def _create_stop(address, lat, lon):
        return StopTime(name=address, lat=lat, lon=lon)

    def _extract_carpool(self, noi_offer) -> Carpool:
        agency = noi_offer['sorigin'].lower()
        offer_id = noi_offer['scode']
        mvalue = noi_offer['mvalue']
        # Note: end_lat_approx and end_lon_approx are not part of mvalue, but only smetadata
        smetadata = noi_offer['smetadata']

        origin = NoiImporter._create_stop(
            mvalue['start_post_code'], mvalue['start_lat_approx'], mvalue['start_lon_approx']
        )
        destination = NoiImporter._create_stop(
            mvalue['end_post_code'], smetadata['end_lat_approx'], smetadata['end_lon_approx']
        )
        startTime = datetime.fromisoformat(mvalue.get('ride_start_at_UTC').replace('Z', '+00:00'))
        if self.test_mode:
            tomorrow = datetime.now() + timedelta(days=1)
            startTime = startTime.replace(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)

        carpool = Carpool(
            id=offer_id,
            agency=agency,
            deeplink='https://ummadum.com/',  # TODO for now, we don't have a call back
            stops=[origin, destination],
            departureTime=startTime.strftime('%H:%M'),
            departureDate=startTime.strftime('%Y-%m-%d'),
            lastUpdated=mvalue.get('ride_created_at_UTC').replace('Z', '+00:00'),
        )

        return carpool

    def load_carpools(self) -> List[Carpool]:
        # noi_carpools_url = config.noi_carpools_url
        # TODO make configurable
        noi_carpools_url = 'https://mobility.api.opendatahub.testingmachine.eu/v2/flat,node/CarpoolingTrip/*/latest'

        where_condition = f'and(sactive.eq.true,sorigin.eq.{self.agency_id})'
        if self.test_mode:
            where_condition = f'sorigin.eq.{self.agency_id}'

        params = {'limit': '-1', 'where': where_condition}

        request_headers = {'accept': 'application/json'}

        try:
            result = requests.get(
                noi_carpools_url,
                headers=request_headers,
                params=params,
            )
            if result.status_code == 200:
                json_results = result.json()
                carpools = [self._extract_carpool(cp) for cp in json_results['data']]
                return carpools
            else:
                logger.error('opendatahub request returned with status_code %s', result.status_code)
                json_results = result.json()
                if 'status' in json_results:
                    logger.error('Error was: %s', result.json()['status'])

                raise ValueError('Sync failed with error. See logs')

        except BaseException as e:
            logger.exception(f'Error on import for agency {self.agency_id}')
            raise e
