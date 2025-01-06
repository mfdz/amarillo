from amarillo.models.Carpool import Carpool, StopTime, Weekday

# TODO use meanigful values for id and lat, lon
stops_1234 = [
    StopTime(
        id="de:08115:4802:0:3",
        name="Herrenberg",
        lat=48.5948979,
        lon=8.8684534),
    StopTime(
        id="de:08111:6221:3:6",
        name="Stuttgart Feuersee",
        lat= 48.7733275,
        lon=9.1671590)]

carpool_1234 = Carpool(
    id="1234",
    agency="mfdz",
    deeplink="https://mfdz.de/trip/1234",
    stops=stops_1234,
    departureTime="07:00",
    departureDate="2022-03-30",
)

carpool_repeating = Carpool(
    id="12345",
    agency="mfdz",
    deeplink="https://mfdz.de/trip/12345",
    stops=stops_1234,
    departureTime="06:00",
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
    'agency': "mfdz",
    'deeplink': "https://mfdz.de/trip/123",
    'stops': [
        {'id': "mfdz:12073:001", 'name': "abc", 'lat': 53.11901, 'lon': 14.015776},
        {'id': "de:12073:900340137::3", 'name': "xyz", 'lat': 53.011459, 'lon': 13.94945}],
    'departureTime': "23:59",
    'departureDate': "2022-05-30",
}

carpool_repeating_json = {
    'id': "Zwei",
    'agency': "mfdz",
    'deeplink': "https://mfdz.de/trip/123",
    'stops': [
        {'id': "mfdz:12073:001", 'name': "abc", 'lat': 53.11901, 'lon': 14.015776},
        {'id': "de:12073:900340137::3", 'name': "xyz", 'lat': 53.011459, 'lon': 13.94945}],
    'departureTime': "15:00",
    'departureDate': ["monday"],
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

stop_issue = {"id": "106727", "agency": "ride2go", "deeplink": "https://ride2go.com/?trip=106727", "stops": [{"id": None, "name": "Mitfahrbank Angerm\u00fcnde, Einkaufscenter, Prenzlauer Stra\u00dfe, 16278 Angerm\u00fcnde", "departureTime": None, "arrivalTime": None, "lat": 53.0220209, "lon": 13.9999447, "pickup_dropoff": None}, {"id": None, "name": "Mitfahrbank B\u00f6lkendorf, B\u00f6lkendorfer Stra\u00dfe, 16278 Angerm\u00fcnde", "departureTime": None, "arrivalTime": None, "lat": 52.949856, "lon": 14.003533, "pickup_dropoff": None}], "departureTime": "17:00:00", "departureDate": "2022-06-22", "path": None, "lastUpdated": "2022-06-22T11:04:22"}

carpool_with_unchanged_stops = Carpool(
    id="1234",
    agency="matchrider",
    deeplink="https://mfdz.de/trip/1234",
    stops=[
        StopTime(
            id="de:08115:4802:0:3",
            name="Herrenberg",
            lat=48.5948979,
            lon=8.8684534,
            departureTime="07:00"),
        StopTime(
            id="de:08111:6221:3:6",
            name="Stuttgart Feuersee",
            lat= 48.7733275,
            lon=9.1671590,
            arrivalTime="07:30"
            )],
    departureTime="07:00",
    departureDate=['monday','tuesday',],
)
