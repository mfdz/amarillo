import os
import json
from glob import glob
from typing import Dict
from app.models.Carpool import Agency, Carpool
from app.services.trips import TripStore
from app.services.stops import StopsStore


class CarpoolService():

    def __init__(self, trip_store):
        self.trip_store = trip_store
        self.carpools: Dict[str, Carpool] = {}
        self.agencies: Dict[str, Agency] = {}

        for agency_file_name in glob('data/agency/*.json'):
            with open(agency_file_name) as agency_file:
                dict = json.load(agency_file)
                agency = Agency(**dict)
                agency_id = agency.id
                self.agencies[agency_id] = agency

    def get(self, agency_id: str, carpool_id: str):
        return self.carpools.get(f"{agency_id}:{carpool_id}")

    def get_all_ids(self):
        return self.carpools.keys()

    def put(self, agency_id: str, carpool_id: str, carpool):
        self.carpools[f"{agency_id}:{carpool_id}"] = carpool
        self.trip_store.put_carpool(carpool)

    def delete(self, agency_id: str, carpool_id: str):
        id = f"{agency_id}:{carpool_id}"
        del self.carpools[id]
        self.trip_store.delete_carpool(id)

    def get_agency(self, agency_id: str) -> Agency:
        agency = self.agencies.get(agency_id)
        return agency
