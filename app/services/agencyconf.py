import json
from glob import glob
from typing import Dict
import logging

from fastapi import HTTPException

from app.models.Carpool import Agency
from app.models.token import Token

logger = logging.getLogger(__name__)


class AgencyConfService:

    def __init__(self):
        # both Dicts to be kept in sync always.
        self.agency_id_to_agency_conf: Dict[str, Token] = {}
        self.api_key_to_agency_id: Dict[str, str] = {}

        for agency_conf_file_name in glob('conf/agencyconf/*.json'):
            with open(agency_conf_file_name) as agency_conf_file:
                dict = json.load(agency_conf_file)
                agency_conf = Token(**dict)
                agency_id = agency_conf.agency_id
                self.agency_id_to_agency_conf[agency_id] = agency_conf
                self.api_key_to_agency_id[agency_conf.token] = agency_conf.agency_id

    def get_agency_conf(self, agency_id: str) -> Token:
        agency_conf = self.agency_id_to_agency_conf.get(agency_id)
        return agency_conf

    def check_api_key(self, api_key: str) -> str:

        agency_id = self.api_key_to_agency_id.get(api_key)

        if agency_id is None:
            logger.error("X-Token header invalid")
            raise HTTPException(status_code=400, detail="X-Token header invalid")

        return agency_id
