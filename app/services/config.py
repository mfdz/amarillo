from pydantic import BaseSettings
from typing import List


class Config(BaseSettings):
    admin_token: str = None
    agencies: List[str] = []
    ride2go_query_data: str
    env: str = 'DEV'


config = Config(_env_file='config', _env_file_encoding='utf-8')
