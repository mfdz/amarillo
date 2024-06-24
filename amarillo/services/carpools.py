import json
import logging
from datetime import datetime
from typing import Dict
from amarillo.models.Carpool import Carpool
from amarillo.services.config import config
from amarillo.services.trips import TripStore
from amarillo.utils.utils import yesterday, is_older_than_days

logger = logging.getLogger(__name__)

class CarpoolService():
    
    def __init__(self, trip_store, max_age_carpool_offers_in_days: int = 180):
        self.max_age_carpool_offers_in_days = max_age_carpool_offers_in_days
        self.trip_store = trip_store
        self.carpools: Dict[str, Carpool] = {}

    def is_outdated(self, carpool):
        """
        A carpool offer is outdated, if 
            * it's completly in the past (if it's a single date offer).
              As we know the start time but not latest arrival, we deem
              offers starting the day before yesterday as outdated
            * it's last update occured before self.max_age_carpool_offers_in_days
        """
        runs_once = not isinstance(carpool.departureDate, set)        
        return (is_older_than_days(carpool.lastUpdated.date(), self.max_age_carpool_offers_in_days) or
            (runs_once and carpool.departureDate < yesterday()))

    def purge_outdated_offers(self):
        """
        Iterates over all carpools and deletes those which are outdated
        """
        for key in list(self.carpools.keys()):
            cp = self.carpools.get(key)
            if cp and self.is_outdated(cp):
                logger.info("Purge outdated offer %s", key)
                self.delete(cp.agency, cp.id)
                try:
                    from amarillo.plugins.metrics import trips_deleted_counter
                    trips_deleted_counter.inc()
                except ImportError:
                    pass

    def get(self, agency_id: str, carpool_id: str):
        return self.carpools.get(f"{agency_id}:{carpool_id}")

    def get_all_ids(self):
        return list(self.carpools)

    def put(self, agency_id: str, carpool_id: str, carpool):
        self.carpools[f"{agency_id}:{carpool_id}"] = carpool
        # Outdated trips (which might have been in the store)
        # will be deleted
        if self.is_outdated(carpool):
            logger.info('Deleting outdated carpool %s:%s', agency_id, carpool_id)
            self.delete(agency_id, carpool_id)
        else:
            self.trip_store.put_carpool(carpool)

    def delete(self, agency_id: str, carpool_id: str):
        id = f"{agency_id}:{carpool_id}"
        if id in self.carpools:
            del self.carpools[id]
        self.trip_store.delete_carpool(agency_id, carpool_id)
