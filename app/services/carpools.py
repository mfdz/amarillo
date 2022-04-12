
from typing import Dict
from app.models.Carpool import Carpool
from app.services.trips import TripStore
from app.services.stops import StopsStore


class CarpoolService():

	carpools: Dict[str, Carpool] = {}

	def __init__(self, trip_store):
		self.trip_store = trip_store

	def get(self, agency_id: str, carpool_id: str):
		return self.carpools.get(f"{agency_id}:{carpool_id}")

	def put(self, agency_id: str, carpool_id: str, carpool):
		self.carpools[f"{agency_id}:{carpool_id}"] = carpool
		self.trip_store.put_carpool(carpool)

	def delete(self, agency_id: str, carpool_id: str):
		id = f"{agency_id}:{carpool_id}"
		del self.carpools[id]
		self.trip_store.delete_carpool(id)
	
carpools = CarpoolService(TripStore(StopsStore()))