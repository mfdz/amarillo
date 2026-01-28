import logging
from datetime import datetime

from amarillo.models.Carpool import Carpool, StopTime
from amarillo.services.importing.amarillo import AmarilloImporter

logger = logging.getLogger(__name__)


class PendlerportalImporter(AmarilloImporter):

    de_en_weekdays_mapping = {
        "Montag": "monday",
        "Dienstag": "tuesday",
        "Mittwoch": "wednesday",
        "Donnerstag": "thursday",
        "Freitag": "friday",
        "Samstag": "saturday",
        "Sonntag": "sunday",
    }

    def __init__(self, url):
        super().__init__("pendlerportal", url)

    def _extract_id(self, offer: dict) -> str:
        # Pendlerportal does not provide an id Attribute,
        # deeplink contains uuid which we use as such
        return offer["deeplink"].rsplit("/", 1)[1]

    def _extract_carpool(self, offer) -> Carpool:
        carpool_id = self._extract_id(offer)
        weekdays = offer.get("weekdays")
        offerDepartureDate = datetime.strptime(offer.get("departDate"), "%d.%m.%Y")
        if isinstance(weekdays, list) and len(weekdays) > 0:
            departureDate = [self.de_en_weekdays_mapping[weekday] for weekday in weekdays]
        else:
            departureDate = offerDepartureDate.strftime("%Y-%m-%d")

        departureTime = offer.get("departTime")
        if departureTime == "":
            logger.debug("Startdate of %s unset, using 06:00", carpool_id)
            departureTime = "06:00"

        deeplink = f"https://{offer['deeplink']}" if not offer["deeplink"].startswith("http") else offer["deeplink"]

        carpool = Carpool(
            id=carpool_id,
            agency=self.agency_id,
            deeplink=deeplink,
            stops=[self._extract_stop(stop) for stop in offer["stops"]],
            departureTime=departureTime,
            departureDate=departureDate,
            lastUpdated=offerDepartureDate,
        )

        return carpool

    @staticmethod
    def _extract_stop(stop):
        return StopTime(
            name=stop["address"],
            lat=stop["coordinates"]["lat"],
            lon=stop["coordinates"]["lon"],
        )
