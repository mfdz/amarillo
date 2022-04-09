from app.services import stops 

def test_load_stops_from_file():
    store = stops.StopsStore()
    store.register_stops("app/tests/stops.csv")
    print(store.stopsDataFrames)

def test_load_stops_from_web_():
    store = stops.StopsStore()
    store.register_stops("https://data.mfdz.de/mfdz/stops/custom.csv")
    print("aa")
    print(store.stopsDataFrames)