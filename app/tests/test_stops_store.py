from app.services import stops 

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
