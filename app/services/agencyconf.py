import json
from glob import glob
from typing import Dict, List
import logging

from fastapi import HTTPException

from app.models.AgencyConf import AgencyConf
from app.services.config import config

logger = logging.getLogger(__name__)
directory = 'data/agencyconf'

class AgencyConfService:

    def __init__(self):
        # Both Dicts to be kept in sync always. The second api_key_to_agency_id is like a reverse
        # cache for the first for fast lookup of valid api keys, which happens on *every* request.
        self.agency_id_to_agency_conf: Dict[str, AgencyConf] = {}
        self.api_key_to_agency_id: Dict[str, str] = {}

        for agency_conf_file_name in glob(f'{directory}/*.json'):
            with open(agency_conf_file_name) as agency_conf_file:
                dict = json.load(agency_conf_file)
                agency_conf = AgencyConf(**dict)
                agency_id = agency_conf.agency_id
                self.agency_id_to_agency_conf[agency_id] = agency_conf
                self.api_key_to_agency_id[agency_conf.api_key] = agency_conf.agency_id

    def get_agency_conf(self, agency_id: str) -> AgencyConf:
        agency_conf = self.agency_id_to_agency_conf.get(agency_id)
        return agency_conf

    def check_api_key(self, api_key: str) -> str:
        """Check if the api key is valid

        The agencies' api keys are checked first, and the admin's key.

        The agency_id is returned for further checks in the caller if the request is permitted,
        like {agency_id} == agency_id
        """

        # TODO FG see in debugger it it works
        key_of_agency = self.api_key_to_agency_id.get(api_key)
        key_of_admin = config.admin_token

        agency_id = key_of_agency or key_of_admin

        if agency_id is None:
            message = "X-Api-Key header invalid"
            logger.error(message)
            raise HTTPException(status_code=400, detail=message)

        return agency_id

    def add(self, agency_conf: AgencyConf) -> AgencyConf:
        logger.info(f"Added configuration for agency {agency_conf.agency_id}.")
        # TODO FG save to file system

    # TODO FG list needed?
    def get_agency_ids(self) -> List[str]:
        return self.agency_id_to_agency_conf.keys()
