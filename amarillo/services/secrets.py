from typing import Dict
from pydantic import Field
from pydantic_settings import BaseSettings

# Example: secrets = { "mfdz": "some secret" }
class Secrets(BaseSettings):
    ride2go_token: str = Field(None, env = 'RIDE2GO_TOKEN')


# Read if file exists, otherwise no error (it's in .gitignore)
secrets = Secrets(_env_file='secrets', _env_file_encoding='utf-8')

