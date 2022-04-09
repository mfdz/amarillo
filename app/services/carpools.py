
from typing import Any, Dict, List
from app.models.Carpool import Carpool

class CarpoolService():

	carpools: Dict[str, Carpool] = {}

	def get(self, agency_id: str, carpool_id: str):
		return self.carpools.get(carpool_id)

	def put(self, agency_id: str, carpool_id: str, carpool):
		self.carpools[carpool_id] = carpool

	def delete(self, agency_id: str, carpool_id: str):
		self.carpools[carpool_id] = None

	def get_recent_deletions(self):
		return []

	def get_recent_updates(self):
		return []
	
carpools = CarpoolService()