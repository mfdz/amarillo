from pydantic import BaseModel, Field


class Token(BaseModel):
    agency_id: str = Field(
        description="ID of the agency that uses this token.",
        min_length=1,
        max_length=20,
        regex='^[a-zA-Z0-9]+$',
        example="mfdz")

    token: str = Field(
        description="The agency's token for using the API",
        min_length=20,
        max_length=20,
        regex=r'^[a-zA-Z0-9]+$',
        example="d8yLuY4DqMEUCLcfJASi")

    class Config:
        schema_extra = {
            "title": "Token",
            "description": "Token for an agency.",
            "example":
                {
                  "agency_id": "mfdz",
                  "token": "d8yLuY4DqMEUCLcfJASi"
                }
        }
