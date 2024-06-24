import json
import os
from glob import glob
from typing import Dict, List
import logging

from fastapi import HTTPException, status

from amarillo.models.User import User
from amarillo.services.config import config
from amarillo.services.passwords import get_password_hash

logger = logging.getLogger(__name__)

user_conf_directory = 'data/users'


class UserService:

    def __init__(self):
        # Both Dicts to be kept in sync always. The second api_key_to_agency_id is like a reverse
        # cache for the first for fast lookup of valid api keys, which happens on *every* request.
        self.user_id_to_user_conf: Dict[str, User] = {}
        self.api_key_to_user_id: Dict[str, str] = {}

        for user_conf_file_name in glob(f'{user_conf_directory}/*.json'):
            with open(user_conf_file_name) as user_conf_file:
                dictionary = json.load(user_conf_file)

                user_conf = User(**dictionary)

                agency_id = user_conf.user_id
                api_key = user_conf.api_key

                self.user_id_to_user_conf[agency_id] = user_conf
                if api_key is not None:
                    self.api_key_to_user_id[api_key] = user_conf.user_id

    def get_user(self, user_id: str) -> User:
        user_conf = self.user_id_to_user_conf.get(user_id)
        return user_conf

    def check_api_key(self, api_key: str) -> str:
        """Check if the API key is valid

        The agencies' api keys are checked first, and the admin's key.

        The agency_id or "admin" is returned for further checks in the caller if the
        request is permitted, like {agency_id} == agency_id.
        """

        agency_id = self.api_key_to_user_id.get(api_key)

        is_agency = agency_id is not None

        if is_agency:
            return agency_id

        is_admin = api_key == config.admin_token

        if is_admin:
            return "admin"

        message = "X-API-Key header invalid"
        logger.error(message)
        raise HTTPException(status_code=400, detail=message)

    def add(self, user_conf: User):

        user_id = user_conf.user_id
        api_key = user_conf.api_key

        agency_id_exists_already = self.user_id_to_user_conf.get(user_id) is not None

        if agency_id_exists_already:
            message = f"Agency {user_id} exists already. To update, delete it first."
            logger.error(message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        agency_using_this_api_key_already = self.api_key_to_user_id.get(api_key)
        a_different_agency_is_using_this_api_key_already = \
            agency_using_this_api_key_already is not None and \
            agency_using_this_api_key_already != user_id

        if a_different_agency_is_using_this_api_key_already:
            message = f"Duplicate API Key for {user_id} not permitted. Use a different key."
            logger.error(message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        user_conf.password = get_password_hash(user_conf.password)

        with open(f'{user_conf_directory}/{user_id}.json', 'w', encoding='utf-8') as f:
            f.write(user_conf.json())

        self.user_id_to_user_conf[user_id] = user_conf
        self.api_key_to_user_id[api_key] = user_id

        logger.info(f"Added configuration for user {user_id}.")

    def get_user_ids(self) -> List[str]:
        return list(self.user_id_to_user_conf.keys())

    def delete(self, user_id):

        user_conf = self.user_id_to_user_conf.get(user_id)

        api_key = user_conf.api_key

        del self.api_key_to_user_id[api_key]

        del self.user_id_to_user_conf[user_id]

        os.remove(f'{user_conf_directory}/{user_id}.json')

        logger.info(f"Deleted configuration for {user_id}.")
