from typing import Dict
from pydantic import BaseSettings, Field

# Example: secrets = { "mfdz": "some secret" }
class Secrets(BaseSettings):
    secrets: Dict[str, str] = Field({})


# Read if file exists, otherwise no error (it's in .gitignore)
secrets = Secrets(_env_file='secrets', _env_file_encoding='utf-8')

