from app.tests.sampledata import cp1, carpool_repeating
from app.services.trips import TripStore
from app.services.stops import StopsStore


import logging
logger = logging.getLogger(__name__)

def test_trip_store_put_one_time_carpool():
    trip_store = TripStore(StopsStore())

    t = trip_store.put_carpool(cp1)
    assert t != None
    assert len(t.stops) >= 2
    assert t.stops.iloc[[0]].values[0][1] == 'mfdz:12073:001'
    assert t.stops.iloc[[-1]].values[0][1] == 'de:12073:900340137::3'

def test_trip_store_put_repeating_carpool():
    trip_store = TripStore(StopsStore())

    t = trip_store.put_carpool(carpool_repeating)
    assert t != None
    assert len(t.stops) >= 2
