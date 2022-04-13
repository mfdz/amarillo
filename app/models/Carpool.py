from datetime import time, date, datetime
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import List, Union, Set, Optional, Tuple
from datetime import time
from pydantic import BaseModel, Field
from enum import Enum

NumType = Union[float, int]

class Weekday(str, Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class StopTime(BaseModel):
    id: str = Field(
        None,
        description="Optional Stop ID. If given, it should conform to the "
                    "IFOPT specification. For official transit stops, "
                    "it should be their official IFOPT. In Germany, this is "
                    "the DHID which is available via the 'zentrales "
                    "Haltestellenverzeichnis (zHV)', published by DELFI e.V. "
                    "Note, that currently carpooling location.",
        regex=r"^([a-zA-Z]{2,5}):\d+:\d+(:\d*(:\w+)?)?$",
        example="de:12073:900340137::2")

    name: str = Field(
        description="Name of the location. Use a name that people will "
                    "understand in the local and tourist vernacular.",
        min_length=1,
        max_length=256,
        example="Angermünde, Breitscheidstr.")

    departureTime: str = Field(
        None,
        description="Departure time from a specific stop for a specific "
                    "carpool trip. For times occurring after midnight on the "
                    "service day, the time is given as a value greater than "
                    "24:00:00 in HH:MM:SS local time for the day on which the "
                    "trip schedule begins. If there are not separate times for "
                    "arrival and departure at a stop, the same value for arrivalTime "
                    "and departureTime. Note, that arrivalTime/departureTime of "
                    "the stops are not mandatory, and might then be estimated by "
                    "this service.",
        regex=r"^[0-9][0-9]:[0-5][0-9](:[0-5][0-9])?$",
        example="17:00"
    )

    arrivalTime: str = Field(
        None,
        description="Arrival time at a specific stop for a specific trip on a "
                    "carpool route. If there are not separate times for arrival "
                    "and departure at a stop, enter the same value for arrivalTime "
                    "and departureTime. For times occurring after midnight on the "
                    "service day, the time as a value greater than 24:00:00 in "
                    "HH:MM:SS local time for the day on which the trip schedule "
                    "begins. Note, that arrivalTime/departureTime of the stops "
                    "are not mandatory, and might then be estimated by this "
                    "service.",
        regex=r"^[0-9][0-9]:[0-5][0-9](:[0-5][0-9])?$",
        example="18:00")

    lat: float = Field(
        description="Latitude of the location. Should describe the location "
                    "where a passenger may mount/dismount the vehicle.",
        ge=-90,
        lt=90,
        multiple_of=1e-10,
        example="53.0137311391")

    lon: float = Field(
        description="Longitude of the location. Should describe the location "
                    "where a passenger may mount/dismount the vehicle.",
        ge=-180,
        lt=180,
        multiple_of=1e-10,
        example="13.9934706687")

    class Config:
        schema_extra = {
            "example": "{'id': 'de:12073:900340137::2', 'name': "
                       "'Angermünde, Breitscheidstr.', 'lat': 53.0137311391, "
                       "'lon': 13.9934706687}"
        }

class Region(BaseModel):
    id: str = Field(
        description="ID of the agency.",
        min_length=1,
        max_length=20,
        regex='^[a-zA-Z0-9]+$',
        example="bb")
    
    bbox: Tuple[NumType, NumType, NumType, NumType] = Field(
        description="ID of the agency.",
        example=[10.5,49.2,11.3,51.3])

class Agency(BaseModel):
    id: str = Field(
        description="ID of the agency.",
        min_length=1,
        max_length=20,
        regex='^[a-zA-Z0-9]+$',
        example="mfdz")

    name: str = Field(
        description="Name",
        min_length=1,
        max_length=48,
        regex=r'^[\w -\.]+$',
        example="MITFAHR|DE|ZENTRALE")

    url: HttpUrl = Field(
        description="URL of the carpool agency.",
        example="https://mfdz.de/")

    timezone: str = Field(
        description="Timezone where the carpool agency is located.",
        min_length=1,
        max_length=48,
        regex=r'^[\w/]+$',
        example="Europe/Berlin")

    lang: str = Field(
        description="Primary language used by this carpool agency.",
        min_length=1,
        max_length=2,
        regex=r'^[a-zA-Z_]+$',
        example="de")

    email: EmailStr = Field(
        description="""Email address actively monitored by the agency’s 
            customer service department. This email address should be a direct 
            contact point where carpool riders can reach a customer service 
            representative at the agency.""",
        example="info@mfdz.de")

    class Config:
        schema_extra = {
            "title": "Agency",
            "description": "Carpool agency.",
            "example":
                """
                {
                  "id": "mfdz",
                  "name": "MITFAHR|DE|ZENTRALE",
                  "url": "http://mfdz.de",
                  "timezone": "Europe/Berlin",
                  "lang": "de",
                  "email": ""info@mfdz.de""
                }
                """
        }

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
            "title": "Carpool",   
            # description ...
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
