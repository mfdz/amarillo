from app.services import stops 
from app.models.Carpool import StopTime

def test_load_stops_from_file():
    store = stops.StopsStore([{"url": "app/tests/stops.csv", "vicinity": 50}])
    store.load_stop_sources()
    assert len(store.stopsDataFrames[0]['stops']) > 0

def test_load_csv_stops_from_web_():
    store = stops.StopsStore([{"url": "https://data.mfdz.de/mfdz/stops/custom.csv", "vicinity": 50}])
    store.load_stop_sources()
    assert len(store.stopsDataFrames[0]['stops']) > 0
    
def test_load_geojson_stops_from_web_():
    store = stops.StopsStore([{"url": "https://datahub.bbnavi.de/export/rideshare_points.geojson", "vicinity": 50}])
    store.load_stop_sources()
    assert len(store.stopsDataFrames[0]['stops']) > 0

def test_find_closest_stop():
    store = stops.StopsStore([{"url": "app/tests/stops.csv", "vicinity": 50}])
    store.load_stop_sources()
    carpool_stop = StopTime(name="start", lat=53.1191, lon=14.01577)
    stop = store.find_closest_stop(carpool_stop, 1000)
    assert stop.name=='Mitfahrbank Biesenbrow'
