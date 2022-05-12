from app.services import stops 

def test_load_stops_from_file():
    store = stops.StopsStore()
    store.register_stops("app/tests/stops.csv")
    assert len(store.stopsDataFrames[0]['stops']) > 0

def test_load_csv_stops_from_web_():
    store = stops.StopsStore()
    store.register_stops("https://data.mfdz.de/mfdz/stops/custom.csv")
    assert len(store.stopsDataFrames[0]['stops']) > 0
    
def test_load_geojson_stops_from_web_():
    store = stops.StopsStore()
    store.register_stops("https://datahub.bbnavi.de/export/rideshare_points.geojson")
    assert len(store.stopsDataFrames[0]['stops']) > 0
