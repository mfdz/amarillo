import json
from glob import glob
from typing import Dict

from app.models.Carpool import Agency


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
