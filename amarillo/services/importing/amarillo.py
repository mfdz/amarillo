import logging
import json
from typing import List

from amarillo.models.Carpool import Carpool, StopTime
from amarillo.utils.get import get

logger = logging.getLogger(__name__)


class AmarilloImporter:

    # In case the remote endpoint returns a dict instead of a list of offers,
    # this key is used to access to list of carpool offers.
    RESPONSE_DICT_OFFERS_KEY = 'data'

    def __init__(self, agency_id, url, http_headers: dict[str, str] = {}):
        self.agency_id = agency_id
        self.carpools_url = str(url)
        self.carpools_http_headers = http_headers

    @staticmethod
    def _extract_stop(stop):
        return StopTime(
            # TODO for now, we ignore ids.
            name=stop['name'],
            lat=stop['lat'],
            lon=stop['lon'],
        )

    def _extract_departure_date(self, offer) -> str | list[str]:
        """
        Returns departureDate. May be subclassed, in case
        carpooling agencies implementation is incompatible
        to the Amarillo model.
        """
        return offer.get("departureDate")

    def _extract_carpool(self, offer) -> Carpool:
        """
        Converts a carpool offer dict into an Amarillo carpool.
        """
        departureDate = self._extract_departure_date(offer)

        carpool = Carpool(
            id=offer["id"],
            agency=self.agency_id,
            deeplink=offer["deeplink"],
            stops=[self._extract_stop(stop) for stop in offer["stops"]],
            departureTime=offer.get("departureTime"),
            departureDate=departureDate,
            exceptionDates=offer.get("exceptionDates"),
            lastUpdated=offer.get("lastUpdated"),
            path=offer.get('path'),
        )
        return carpool

    def _get_data(self):
        """
        Requests carpool offers for carpools url.
        The url may be provided as a file:// url to allow
        unit testing.
        """
        if self.carpools_url.startswith("file://"):
            with open(self.carpools_url[7:], "r") as f:
                result = json.load(f)
        else:
            response = get(self.carpools_url, headers=self.carpools_http_headers, timeout=60)
            result = response.json()

        return result

    def _get_data_from_json_response(self, json_response):
        # Extract from json response offers arrays.
        return json_response.get(self.RESPONSE_DICT_OFFERS_KEY) if isinstance(json_response, dict) else json_response

    def _offers_raw(self):
        for cp in self._get_data_from_json_response(self._get_data()):
            yield cp

    def load_carpools(self) -> List[Carpool]:
        carpools = []
        for cp in self._offers_raw():
            try:
                carpools.append(self._extract_carpool(cp))
            except BaseException as e:
                logger.exception(f"Error on import for agency {self.agency_id} {cp}", e)
                continue

        return carpools
