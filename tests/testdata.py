from models.Carpool import Carpool
from models.StopTime import StopTime

stops0 = [StopTime(id="de:12073:900340137::6", name="qwert", lat=45, lon=10),
          StopTime(id="de:12073:900340137::7", name="dd", lat=45, lon=10)]

cp0 = Carpool(
    id="dieNull",
    agency="a",
    deeplink="https://ride2go.com/trip/123",
    stops=stops0,
    departureTime="15:00",
    departureDate="2022-03-30",
)

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
