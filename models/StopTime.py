from datetime import time
from pydantic import BaseModel, Field


class StopTime(BaseModel):
    id: str = Field(
        None,
        description="Optional Stop ID. If given, it should conform to the "
                    "IFOPT specification. For official transit stops, "
                    "it should be their official IFOPT. In Germany, this is "
                    "the DHID which is available via the 'zentrales "
                    "Haltestellenverzeichnis (zHV)', published by DELFI e.V. "
                    "Note, that currently carpooling location.",
        regex="^([a-zA-Z]{2,5}):\d+:\d+:\d*:\w+$",
        example="de:12073:900340137::2")

    name: str = Field(
        description="Name of the location. Use a name that people will "
                    "understand in the local and tourist vernacular.",
        min_length=1,
        max_length=256,
        example="Angermünde, Breitscheidstr.")

    departureTime: time = Field(
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
        # TODO see below
        # regex="^[0-9][0-9]:[0-5][0-9](:[0-5][0-9])?$",
        example="17:00"
    )

    arrivalTime: time = Field(
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
        # TODO the regexp will probably not work if the time is >24:00 because
        # the type is time. Handle internal and external representation
        # differently?
        # Actually, when commented it, it causes this error:
        # ValueError: On field "arrivalTime" the following field constraints are
        # set but not enforced: regex.
        # regex="^[0-9][0-9]:[0-5][0-9](:[0-5][0-9])?$",
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
