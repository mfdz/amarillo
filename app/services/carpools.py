
from typing import Dict
from app.models.Carpool import Carpool
from app.services.trips import trip_store

class CarpoolService():

	carpools: Dict[str, Carpool] = {}

	def get(self, agency_id: str, carpool_id: str):
		return self.carpools.get(f"{agency_id}:{carpool_id}")

	def put(self, agency_id: str, carpool_id: str, carpool):
		self.carpools[f"{agency_id}:{carpool_id}"] = carpool
		trip_store.put_carpool(carpool)

	def delete(self, agency_id: str, carpool_id: str):
		id = f"{agency_id}:{carpool_id}"
		self.carpools[id] = None
		trip_store.delete_carpool(id)
	
carpools = CarpoolService()