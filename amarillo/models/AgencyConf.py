from pydantic import ConfigDict, BaseModel, Field


class AgencyConf(BaseModel):
    agency_id: str = Field(
        description="ID of the agency that uses this token.",
        min_length=1,
        max_length=20,
        pattern=r'^[a-zA-Z0-9]+$',
        examples=["mfdz"])

    api_key: str = Field(
        description="The agency's API key for using the API",
        min_length=20,
        max_length=256,
        pattern=r'^[a-zA-Z0-9]+$',
        examples=["d8yLuY4DqMEUCLcfJASi"])

    add_dropoffs_and_pickups: bool = Field(
        description="Should Amarillo add pickup/dropoff points along the route?",
        default=True,
        examples=[False])

    replace_carpool_stops_by_closest_transit_stops: bool = Field(
        description="Should Amarillo replace carpool stops by closest transit stops? Should be True for agencies allowing origin/destination addresses to provide privacy.",
        default=True,
        examples=[True])

    model_config = ConfigDict(json_schema_extra={
        "title": "Agency Configuration",
        "description": "Configuration for an agency.",
        "example":
            {
                "agency_id": "mfdz",
                "api_key": "d8yLuY4DqMEUCLcfJASi",
                "add_dropoffs_and_pickups": True
            }
    })
