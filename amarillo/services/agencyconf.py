import json
import os
from glob import glob
from typing import Dict, List
import logging

from fastapi import HTTPException, status

from amarillo.models.AgencyConf import AgencyConf
from amarillo.services.config import config

logger = logging.getLogger(__name__)

agency_conf_directory = 'data/agencyconf'


class AgencyConfService:

    def __init__(self):
        # Both Dicts to be kept in sync always. The second api_key_to_agency_id is like a reverse
        # cache for the first for fast lookup of valid api keys, which happens on *every* request.
        self.agency_id_to_agency_conf: Dict[str, AgencyConf] = {}
        self.api_key_to_agency_id: Dict[str, str] = {}

        for agency_conf_file_name in glob(f'{agency_conf_directory}/*.json'):
            with open(agency_conf_file_name) as agency_conf_file:
                dictionary = json.load(agency_conf_file)

                agency_conf = AgencyConf(**dictionary)

                agency_id = agency_conf.agency_id
                api_key = agency_conf.api_key

                self.agency_id_to_agency_conf[agency_id] = agency_conf
                self.api_key_to_agency_id[api_key] = agency_conf.agency_id

    def get_agency_conf(self, agency_id: str) -> AgencyConf:
        agency_conf = self.agency_id_to_agency_conf.get(agency_id)
        return agency_conf

    def check_api_key(self, api_key: str) -> str:
        """Check if the API key is valid

        The agencies' api keys are checked first, and the admin's key.

        The agency_id or "admin" is returned for further checks in the caller if the
        request is permitted, like {agency_id} == agency_id.
        """

        agency_id = self.api_key_to_agency_id.get(api_key)

        is_agency = agency_id is not None

        if is_agency:
            return agency_id

        is_admin = api_key == config.admin_token

        if is_admin:
            return "admin"

        message = "X-API-Key header invalid"
        logger.error(message)
        raise HTTPException(status_code=400, detail=message)

    def add(self, agency_conf: AgencyConf):

        agency_id = agency_conf.agency_id
        api_key = agency_conf.api_key

        agency_id_exists_already = self.agency_id_to_agency_conf.get(agency_id) is not None

        if agency_id_exists_already:
            message = f"Agency {agency_id} exists already. To update, delete it first."
            logger.error(message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        agency_using_this_api_key_already = self.api_key_to_agency_id.get(api_key)
        a_different_agency_is_using_this_api_key_already = \
            agency_using_this_api_key_already is not None and \
            agency_using_this_api_key_already != agency_id

        if a_different_agency_is_using_this_api_key_already:
            message = f"Duplicate API Key for {agency_id} not permitted. Use a different key."
            logger.error(message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        with open(f'{agency_conf_directory}/{agency_id}.json', 'w', encoding='utf-8') as f:
            f.write(agency_conf.json())

        self.agency_id_to_agency_conf[agency_id] = agency_conf
        self.api_key_to_agency_id[api_key] = agency_id

        logger.info(f"Added configuration for agency {agency_id}.")

    def get_agency_ids(self) -> List[str]:
        return list(self.agency_id_to_agency_conf.keys())

    def delete(self, agency_id):

        agency_conf = self.agency_id_to_agency_conf.get(agency_id)

        api_key = agency_conf.api_key

        del self.api_key_to_agency_id[api_key]

        del self.agency_id_to_agency_conf[agency_id]

        os.remove(f'{agency_conf_directory}/{agency_id}.json')

        logger.info(f"Deleted configuration for agency {agency_id}.")
