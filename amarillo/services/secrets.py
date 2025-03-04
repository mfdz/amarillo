from typing import Dict, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

# Example: secrets = { "mfdz": "some secret" }
class Secrets(BaseSettings):
    ride2go_token: str = Field(None)
    bessermitfahren_url: Optional[str] = Field(None)
    pendlerportal_url: Optional[str] = Field(None)
    mycarpoolapp_url: Optional[str] = Field(None)

    # TODO: admin_token should be moved here instead of config


# Read if file exists, otherwise no error (it's in .gitignore)
secrets = Secrets(_env_file='secrets', _env_file_encoding='utf-8')

