from models.Carpool import Carpool
from models.StopTime import StopTime
from models.Weekday import Weekday

# TODO use meanigful values for id and lat, lon
stops_1234 = [
    StopTime(
        id="de:12073:900340137::6",
        name="Herrenberg",
        lat=45,
        lon=10),
    StopTime(
        id="de:12073:900340137::7",
        name="Stuttgart",
        lat=45,
        lon=10)]

carpool_1234 = Carpool(
    id="1234",
    agency="mfdz",
    deeplink="https://mfdz.de/trip/1234",
    stops=stops_1234,
    departureTime="7:00",
    departureDate="2022-03-30",
)

carpool_repeating = Carpool(
    id="12345",
    agency="mfdz",
    deeplink="https://mfdz.de/trip/12345",
    stops=stops_1234,
    departureTime="6:00",
    departureDate=[Weekday.monday, Weekday.tuesday, Weekday.wednesday,
                   Weekday.thursday, Weekday.friday],
)

examples = {
    "one-time trip with date": {
        "summary": "one-time trip with date",
        "description": "carpool object that should to be added or modified",
        "value": carpool_1234},
    "repeating trip Mon-Fri": {
        "summary": "repeating trip Mon-Fri",
        "description": "carpool object that should to be added or modified",
        "value": carpool_repeating}
}

data1 = {
    'id': "Eins",
    'agency': "ride2go",
    'deeplink': "https://ride2go.com/trip/123",
    'stops': [
        {'id': "de:12073:900340137::2", 'name': "abc", 'lat': 45, 'lon': 9},
        {'id': "de:12073:900340137::3", 'name': "xyz", 'lat': 45, 'lon': 9}],
    'departureTime': "15:00",
    'departureDate': "2022-03-30",
}

cp1 = Carpool(**data1)

# JSON string for trying out the API in Swagger
cp2 = """
{
  "id": "Vier",
  "agency": "string",
  "deeplink": "http://mfdz.de",
  "stops": [
    {
      "id": "de:12073:900340137::4", "name": "drei", "lat": 45, "lon": 9
    },
    {
      "id": "de:12073:900340137::5", "name": "drei b", "lat": 45, "lon": 9
    }
  ],
  "departureTime": "12:34",
  "departureDate": "2022-03-30",
  "lastUpdated": "2022-03-30 12:34"
}
"""
