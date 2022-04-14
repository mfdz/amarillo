from typing import List

import requests
from app.models.Carpool import Carpool, StopTime
from app.services.secrets import secrets
import re


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
                      departureDate=dict.get('departDate') if dict.get('departDate') else dict.get('weekdays'))

    return carpool

def import_ride2go() -> List[Carpool]:
    # TODO for now. we use braandenburg bounding box, the region filtering should be done on export
    ride2go_query_data = '{ "southWestCoordinates": { "lat": 51.36, "lon": 11.26 }, "northEastCoordinates": { "lat": 53.56, "lon": 14.77 }, "lastModifiedSinceDays": 180 }'

    ride2go_url = "https://ride2go.com/api/v1/trips/export"

    api_key = secrets.secrets.get('ride2go')

    ride2go_headers = {
        'Content-type': 'text/plain;charset=UTF-8',
        'X-API-Key': f"{api_key}"
    }

    try:
        results = requests.get(
            ride2go_url,
            data=ride2go_query_data,
            headers=ride2go_headers
        ).json()

        carpools = [as_Carpool(cp) for cp in results]

        return carpools

    except BaseException as e:
        print(e)  # TODO add logging
        raise e  # TODO handle better
