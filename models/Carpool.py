from datetime import time, date, datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Union, Set, Optional

from models.StopTime import StopTime
from models.Weekday import Weekday


class Carpool(BaseModel):
    id: str = Field(
        description="ID of the carpool. Should be supplied and managed by the "
                    "carpooling platform which originally published this "
                    "offer.",
        min_length=1,
        max_length=256,
        regex='^[a-zA-Z0-9_-]+$',
        example="103361")

    agency: str = Field(
        description="Short one string name of the agency, used as a namespace "
                    "for ids.",
        min_length=1,
        max_length=20,
        regex='^[a-zA-Z0-9]+$',
        example="mfdz")

    deeplink: HttpUrl = Field(
        description="Link to an information page providing detail information "
                    "for this offer, and, especially, an option to book the "
                    "trip/contact the driver.",
        example="https://mfdz.de/trip/103361")

    stops: List[StopTime] = Field(
        ...,
        min_items=2,
        max_items=10,
        description="Stops which this carpool passes by and offers to pick "
                    "up/drop off passengers. This list must at minimum "
                    "include two stops, the origin and destination of this "
                    "carpool trip. Note that for privacy reasons, the stops "
                    "usually should be official locations, like meeting "
                    "points, carpool parkings, ridesharing benches or "
                    "similar.",
        example="""[
                     {
                       "id": "03", 
                       "name": "drei", 
                       "lat": 45, 
                       "lon": 9
                     },
                     {
                       "id": "03b", 
                       "name": "drei b", 
                       "lat": 45, 
                       "lon": 9
                     }
                   ]""")

    departureTime: time = Field(
        description="Time when the carpool leaves at the first stop. Note, "
                    "that this API currently does not support flexible time "
                    "windows for departure, though drivers might be flexible."
                    "For recurring trips, the weekdays this trip will run. ",
        example="17:00")

    departureDate: Union[date, Set[Weekday]] = Field(
        description="Date when the trip will start, in case it is a one-time "
                    "trip. For recurring trips, specify weekdays. "
                    "Note, that when for different weekdays different "
                    "departureTimes apply, multiple carpool offers should be "
                    "published.",
        example='A single date 2022-04-04 or a list of weekdays ["saturday", '
                '"sunday"]')

    lastUpdated: Optional[datetime] = Field(
        None,
        description="LastUpdated should reflect the last time, the user "
                    "providing this offer, made an update or confirmed, "
                    "the offer is still valid. Note that this service might "
                    "purge outdated offers (e.g. older than 180 days). If not "
                    "passed, the service may assume 'now'",
        example="2022-02-13T20:20:39+00:00")

    class Config:
        schema_extra = {
            "example":
                """
                {
                  "id": "1234",
                  "agency": "mfdz",
                  "deeplink": "http://mfdz.de",
                  "stops": [
                    {
                      "id": "de:12073:900340137::2", "name": "ABC", 
                      "lat": 45, "lon": 9
                    },
                    {
                      "id": "de:12073:900340137::3", "name": "XYZ", 
                      "lat": 45, "lon": 9
                    }
                  ],
                  "departureTime": "12:34",
                  "departureDate": "2022-03-30",
                  "lastUpdated": "2022-03-30 12:34"
                }
                """
        }
