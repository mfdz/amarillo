from pydantic import BaseModel, Field


class AgencyConf(BaseModel):
    agency_id: str = Field(
        description="ID of the agency that uses this token.",
        min_length=1,
        max_length=20,
        regex='^[a-zA-Z0-9]+$',
        example="mfdz")

    api_key: str = Field(
        description="The agency's API key for using the API",
        min_length=20,
        max_length=20,
        regex=r'^[a-zA-Z0-9]+$',
        example="d8yLuY4DqMEUCLcfJASi")

    class Config:
        schema_extra = {
            "title": "Agency Configuration",
            "description": "Configuration for an agency.",
            "example":
                {
                    "agency_id": "mfdz",
                    "api_key": "d8yLuY4DqMEUCLcfJASi"
                }
        }
