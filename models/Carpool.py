from datetime import time, date, datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Union, Set, Optional

from models.StopTime import StopTime
from models.Weekday import Weekday

class Carpool(BaseModel):
    id: str = Field(min_length=1, max_length=256, regex='^\\w*$')
    agency: str = Field(..., example="ride2go")
    deeplink: HttpUrl
    stops: List[StopTime] = Field([], min_items=2, max_items=10,
                                  description="""The first stop is the origin of the trip. The last stop is
                                  the destination of the trip.""")
    departureTime: time
    departureDate: Union[date, Set[Weekday]]
    lastUpdated: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                'id': "Eins",
                'agency': "ride2go",
                'deeplink': "https://ride2go.com/trip/123",
                'stops': [{'id': "asdf", 'name': "qewrt", 'lat': 45, 'lon': 9},
                          {'id': "yy", 'name': "zzz", 'lat': 45, 'lon': 9}],
                'departureTime': "15:00",
                'departureDate': "2022-03-30",
            }
        }