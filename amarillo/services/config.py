from typing import List
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    amarillo_baseurl: str = 'http://localhost:8000/'
    admin_token: str
    ride2go_query_data: str
    env: str = 'DEV'
    graphhopper_base_url: str = 'https://api.mfdz.de/gh'
    stop_sources_file: str = 'data/stop_sources.json'
    enhancer_url: str = 'http://localhost:8001'

    # not sure if this is still needed here
    max_age_carpool_offers_in_days: int = 180

config = Config(_env_file='config', _env_file_encoding='utf-8')
