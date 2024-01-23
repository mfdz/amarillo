import json
from glob import glob
from typing import Dict

from amarillo.models.Carpool import Agency

# TODO FG HB this service should also listen to pyinotify
# because the (updated) agencies are needed in the enhancer
# as well.

class AgencyService:

    def __init__(self):
        self.agencies: Dict[str, Agency] = {}

        for agency_file_name in glob('conf/agency/*.json'):
            with open(agency_file_name) as agency_file:
                dict = json.load(agency_file)
                agency = Agency(**dict)
                agency_id = agency.id
                self.agencies[agency_id] = agency

    def get_agency(self, agency_id: str) -> Agency:
        agency = self.agencies.get(agency_id)
        return agency
