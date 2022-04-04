from datetime import time
from pydantic import BaseModel, Field

class StopTime(BaseModel):
    id: str = None
    name: str
    arrivalTime: time = None
    departureTime: time = None # in GTFS time can be >24:00
    lat: float = Field(ge=-90, lt=90, multiple_of=1e-10)
    lon: float = Field(ge=-180, lt=180, multiple_of=1e-10)

    class Config:
        schema_extra = {
            "example": {'id': "asdf", 'name': "qewrt", 'lat': 45, 'lon': 9}
        }