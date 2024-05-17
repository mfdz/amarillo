from typing import Optional
from pydantic import ConfigDict, BaseModel, Field

class User(BaseModel):
    #TODO: add attributes admin, permissions, fullname, email

    user_id: str = Field(
        description="ID of the agency that uses this token.",
        min_length=1,
        max_length=20,
        pattern='^[a-zA-Z0-9]+$',
        examples=["mfdz"])

    api_key: Optional[str] = Field(None,
        description="The agency's API key for using the API",
        min_length=20,
        max_length=256,
        pattern=r'^[a-zA-Z0-9]+$',
        examples=["d8yLuY4DqMEUCLcfJASi"])
    password: Optional[str] = Field(None,
        description="The agency's password for generating JWT tokens",
        min_length=8,
        max_length=256,
        examples=["$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"])
    model_config = ConfigDict(json_schema_extra={
        "title": "Agency Configuration",
        "description": "Configuration for an agency.",
        "example":
            {
                "agency_id": "mfdz",
                "api_key": "d8yLuY4DqMEUCLcfJASi",
                "password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
            }
    })