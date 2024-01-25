from typing import Dict
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional
# Example: secrets = { "mfdz": "some secret" }
class Secrets(BaseSettings):
    ride2go_token: str = Field(None, env = 'RIDE2GO_TOKEN')
    # TODO: define these as required if metrics plugin is installed
    metrics_user: Optional[str] = Field(None, env = 'METRICS_USER')
    metrics_password: Optional[str] = Field(None, env = 'METRICS_PASSWORD')


# Read if file exists, otherwise no error (it's in .gitignore)
secrets = Secrets(_env_file='secrets', _env_file_encoding='utf-8')

