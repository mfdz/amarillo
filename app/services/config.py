from typing import List
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    admin_token: str
    ride2go_query_data: str
    env: str = 'DEV'


config = Config(_env_file='config', _env_file_encoding='utf-8')
