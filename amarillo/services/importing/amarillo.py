import logging
import json
from typing import List

from amarillo.models.Carpool import Carpool, StopTime
from amarillo.utils.get import get

logger = logging.getLogger(__name__)


class AmarilloImporter:

    def __init__(self, agency_id, url):
        self.agency_id = agency_id
        self.carpools_url = url

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
            response = get(self.carpools_url)
            result = response.json()

        return result

    def _get_data_from_json_response(self, json_response):
        # Extract from json response offers arrays.

        return json_response

    def load_carpools(self) -> List[Carpool]:
        carpools = []
        for cp in self._get_data_from_json_response(self._get_data()):
            try:
                carpools.append(self._extract_carpool(cp))
            except:
                logger.exception(f"Error on import for agency {self.agency_id} {cp}")
                raise

        return carpools
