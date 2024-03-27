from datetime import time, date, datetime
from pydantic import ConfigDict, BaseModel, Field, HttpUrl, EmailStr
from typing import List, Union, Set, Optional, Tuple
from datetime import time
from pydantic import BaseModel, Field
from geojson_pydantic.geometries import LineString
from enum import Enum, IntEnum

NumType = Union[float, int]

MAX_STOPS_PER_TRIP = 100

class Weekday(str, Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"

class PickupDropoffType(str, Enum):
    pickup_and_dropoff = "pickup_and_dropoff"
    only_pickup = "only_pickup"
    only_dropoff = "only_dropoff"

class YesNoEnum(IntEnum):
    yes = 1
    no = 2

class LuggageSize(IntEnum):
    small = 1
    medium = 2
    large = 3

class StopTime(BaseModel):
    id: Optional[str] = Field(
        None,
        description="Optional Stop ID. If given, it should conform to the "
                    "IFOPT specification. For official transit stops, "
                    "it should be their official IFOPT. In Germany, this is "
                    "the DHID which is available via the 'zentrales "
                    "Haltestellenverzeichnis (zHV)', published by DELFI e.V. "
                    "Note, that currently carpooling location.",
        # TODO: usually, ifopts should start with country code. sta GTFS uses Parentit, so we extend to max 8 chars
        pattern=r"^([a-zA-Z]{2,8}):\d+:\d+(:\d*(:\w+)?)?$|^osm:[nwr]\d+$",
        examples=["de:12073:900340137::2"])

    name: str = Field(
        description="Name of the location. Use a name that people will "
                    "understand in the local and tourist vernacular.",
        min_length=1,
        max_length=256,
        examples=["Angermünde, Breitscheidstr."])

    departureTime: Optional[str] = Field(
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
        pattern=r"^[0-9][0-9]:[0-5][0-9](:[0-5][0-9])?$",
        examples=["17:00"]
    )

    arrivalTime: Optional[str] = Field(
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
        pattern=r"^[0-9][0-9]:[0-5][0-9](:[0-5][0-9])?$",
        examples=["18:00"])

    lat: float = Field(
        description="Latitude of the location. Should describe the location "
                    "where a passenger may mount/dismount the vehicle.",
        ge=-90,
        lt=90,
        examples=["53.0137311391"])

    lon: float = Field(
        description="Longitude of the location. Should describe the location "
                    "where a passenger may mount/dismount the vehicle.",
        ge=-180,
        lt=180,
        examples=["13.9934706687"])

    pickup_dropoff: Optional[PickupDropoffType] = Field(
        None, description="If passengers may be picked up, dropped off or both at this stop. "
                "If not specified, this service may assign this according to some custom rules. "
                "E.g. Amarillo may allow pickup only for the first third of the distance travelled, "
                "and dropoff only for the last third." ,
        examples=["only_pickup"]
        )
    model_config = ConfigDict(json_schema_extra={
        "example": "{'id': 'de:12073:900340137::2', 'name': "
                   "'Angermünde, Breitscheidstr.', 'lat': 53.0137311391, "
                   "'lon': 13.9934706687}"
    })

class Region(BaseModel):
    id: str = Field(
        description="ID of the region.",
        min_length=1,
        max_length=20,
        pattern='^[a-zA-Z0-9]+$',
        examples=["bb"])
    
    bbox: Tuple[NumType, NumType, NumType, NumType] = Field(
        description="Bounding box of the region. Format is [minLon, minLat, maxLon, maxLat]",
        examples=[[10.5,49.2,11.3,51.3]])
    
class RidesharingInfo(BaseModel):
    number_free_seats: int = Field(
        description="Number of free seats",
        ge=0,
        examples=[3])
    
    same_gender: Optional[YesNoEnum] = Field(
        None, 
        description="Trip only for same gender:"
                    "1: Yes"
                    "2: No",
        examples=[1])
    luggage_size: Optional[LuggageSize] = Field(
        None, 
        description="Size of the luggage:"
                    "1: small"
                    "2: medium"
                    "3: large",
        examples=[3])
    animal_car: Optional[YesNoEnum] = Field(
        None, 
        description="Animals in Car allowed:"
                    "1: Yes"
                    "2: No",
        examples=[2])

    car_model: Optional[str] = Field(
        None,
        description="Car model",
        min_length=1,
        max_length=48,
        examples=["Golf"])
    car_brand: Optional[str] = Field(
        None,
        description="Car brand",
        min_length=1,
        max_length=48,
        examples=["VW"])
    
    creation_date: datetime = Field(
        description="Date when trip was created",
        examples=["2022-02-13T20:20:39+00:00"])
    
    smoking: Optional[YesNoEnum] = Field(
        None, 
        description="Smoking allowed:"
                    "1: Yes"
                    "2: No",
        examples=[2])
    
    payment_method: Optional[str] = Field(
        None,
        description="Method of payment",
        min_length=1,
        max_length=48)

class Driver(BaseModel):
    driver_id: Optional[str] = Field(
        None,
        description="Identifies the driver.",
        min_length=1,
        max_length=256,
        pattern='^[a-zA-Z0-9_-]+$',
        examples=["789"])
    profile_picture: Optional[HttpUrl] = Field(
        None,
        description="URL that contains the profile picture",
        examples=["https://mfdz.de/driver/789/picture"])
    rating: Optional[int] = Field(
        None,
        description="Rating of the driver from 1 to 5."
                    "0 no rating yet",
        ge=0,
        le=5,
        examples=[5])
    
class Agency(BaseModel):
    id: str = Field(
        description="ID of the agency.",
        min_length=1,
        max_length=20,
        pattern='^[a-zA-Z0-9]+$',
        examples=["mfdz"])

    name: str = Field(
        description="Name",
        min_length=1,
        max_length=48,
        pattern=r'^[\w -\.\|]+$',
        examples=["MITFAHR|DE|ZENTRALE"])

    url: HttpUrl = Field(
        description="URL of the carpool agency.",
        examples=["https://mfdz.de/"])

    timezone: str = Field(
        description="Timezone where the carpool agency is located.",
        min_length=1,
        max_length=48,
        pattern=r'^[\w/]+$',
        examples=["Europe/Berlin"])

    lang: str = Field(
        description="Primary language used by this carpool agency.",
        min_length=1,
        max_length=2,
        pattern=r'^[a-zA-Z_]+$',
        examples=["de"])

    email: EmailStr = Field(
        description="""Email address actively monitored by the agency’s 
            customer service department. This email address should be a direct 
            contact point where carpool riders can reach a customer service 
            representative at the agency.""",
        examples=["info@mfdz.de"])

    terms_url: Optional[HttpUrl] = Field(
        None, description="""A fully qualified URL pointing to the terms of service 
        (also often called "terms of use" or "terms and conditions") 
        for the service.""",
        examples=["https://mfdz.de/nutzungsbedingungen"])

    privacy_url: Optional[HttpUrl] = Field(
        None, description="""A fully qualified URL pointing to the privacy policy for the service.""",
        examples=["https://mfdz.de/datenschutz"])
    model_config = ConfigDict(json_schema_extra={
        "title": "Agency",
        "description": "Carpool agency.",
        "example":
            #"""
            {
              "id": "mfdz",
              "name": "MITFAHR|DE|ZENTRALE",
              "url": "http://mfdz.de",
              "timezone": "Europe/Berlin",
              "lang": "de",
              "email": "info@mfdz.de",
              "terms_url": "https://mfdz.de/nutzungsbedingungen",
              "privacy_url": "https://mfdz.de/datenschutz",
            }
            #"""
    })

class Carpool(BaseModel):
    id: str = Field(
        description="ID of the carpool. Should be supplied and managed by the "
                    "carpooling platform which originally published this "
                    "offer.",
        min_length=1,
        max_length=256,
        pattern='^[a-zA-Z0-9_-]+$',
        examples=["103361"])

    agency: str = Field(
        description="Short one string name of the agency, used as a namespace "
                    "for ids.",
        min_length=1,
        max_length=20,
        pattern='^[a-zA-Z0-9]+$',
        examples=["mfdz"])
    
    driver: Optional[Driver] = Field(
        None, 
        description="Driver data", 
        examples=["""
                {
                    "driver_id": "123", 
                    "profile_picture": "https://mfdz.de/driver/789/picture",
                    "rating": 5
                }
                """])

    deeplink: HttpUrl = Field(
        description="Link to an information page providing detail information "
                    "for this offer, and, especially, an option to book the "
                    "trip/contact the driver.",
        examples=["https://mfdz.de/trip/103361"])

    stops: List[StopTime] = Field(
        ...,
        min_length=2,
        max_length=MAX_STOPS_PER_TRIP,
        description="Stops which this carpool passes by and offers to pick "
                    "up/drop off passengers. This list must at minimum "
                    "include two stops, the origin and destination of this "
                    "carpool trip. Note that for privacy reasons, the stops "
                    "usually should be official locations, like meeting "
                    "points, carpool parkings, ridesharing benches or "
                    "similar.",
        examples=["""[
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
                   ]"""])

    # TODO can be removed, as first stop has departureTime as well
    departureTime: time = Field(
        description="Time when the carpool leaves at the first stop. Note, "
                    "that this API currently does not support flexible time "
                    "windows for departure, though drivers might be flexible."
                    "For recurring trips, the weekdays this trip will run. ",
        examples=["17:00"])

    # TODO think about using googlecal Format
    departureDate: Union[date, Set[Weekday]] = Field(
        description="Date when the trip will start, in case it is a one-time "
                    "trip. For recurring trips, specify weekdays. "
                    "Note, that when for different weekdays different "
                    "departureTimes apply, multiple carpool offers should be "
                    "published.",
        examples=['A single date 2022-04-04 or a list of weekdays ["saturday", '
                '"sunday"]'])

    path: Optional[LineString] = Field(
        None, description="Optional route geometry as json LineString.")
    
    lastUpdated: Optional[datetime] = Field(
        None,
        description="LastUpdated should reflect the last time, the user "
                    "providing this offer, made an update or confirmed, "
                    "the offer is still valid. Note that this service might "
                    "purge outdated offers (e.g. older than 180 days). If not "
                    "passed, the service may assume 'now'",
        examples=["2022-02-13T20:20:39+00:00"])
    additional_ridesharing_info: Optional[RidesharingInfo] = Field(
        None, 
        description="Extension of GRFS to the GTFS standard", 
        examples=["""
                {
                    "number_free_seats": 2, 
                    "creation_date": "2022-02-13T20:20:39+00:00", 
                    "same_gender": 2,
                    "smoking": 1,
                    "luggage_size": 3
                }
                """])
    model_config = ConfigDict(json_schema_extra={
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
                  "lastUpdated": "2022-03-30T12:34:00+00:00"
                }
                """
        })
