from typing import List
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    amarillo_baseurl: str = 'http://localhost:8000/'
    admin_token: str
    ride2go_query_data: str
    env: str = 'DEV'
    graphhopper_base_url: str = 'https://api.mfdz.de/gh'
    stop_sources_file: str = 'conf/stop_sources.json'
    max_age_carpool_offers_in_days: int = 180
    # Syn per default at 11:30pm so all updates are done at midnight
    # when gtfs re-generation will happen
    daily_sync_time: str = '23:00'

config = Config(_env_file='config', _env_file_encoding='utf-8')
