import logging
from typing import List

import requests
from amarillo.models.Carpool import Carpool, StopTime
from amarillo.services.config import config

from amarillo.services.secrets import secrets
import re

logger = logging.getLogger(__name__)

def as_StopTime(stop):
    return StopTime(
        # id="todo",
        name=stop['address'],
        lat=stop['coordinates']['lat'],
        lon=stop['coordinates']['lon']
    )


def as_Carpool(dict) -> Carpool:
    (agency, id) = re.findall(r'https?://(.*)\..*/?trip=([0-9]+)', dict['deeplink'])[0]

    carpool = Carpool(id=id,
                      agency=agency,
                      deeplink=dict['deeplink'],
                      stops=[as_StopTime(s) for s in dict.get('stops')],
                      departureTime=dict.get('departTime'),
                      departureDate=dict.get('departDate') if dict.get('departDate') else dict.get('weekdays'),
                      lastUpdated=dict.get('lastUpdated'))

    return carpool

def import_ride2go() -> List[Carpool]:
    ride2go_query_data = config.ride2go_query_data

    ride2go_url = "https://ride2go.com/api/v1/trips/export"

    api_key = secrets.ride2go_token

    ride2go_headers = {
        'Content-type': 'text/plain;charset=UTF-8',
        'X-API-Key': f"{api_key}"
    }

    try:
        result = requests.get(
            ride2go_url,
            data=ride2go_query_data,
            headers=ride2go_headers
        )
        if result.status_code == 200:
            json_results = result.json()
            carpools = [as_Carpool(cp) for cp in json_results]

            return carpools
        else:
            logger.error("ride2go request returned with status_code %s", result.status_code)
            json_results = result.json()
            if 'status' in json_results:
                logger.error("Error was: %s", result.json()['status'])
            
            raise ValueError("Sync failed with error. See logs") 

    except BaseException as e:
        logger.exception("Error on import for agency ride2go")
        raise e
