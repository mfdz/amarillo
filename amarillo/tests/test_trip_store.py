from amarillo.tests.sampledata import cp1, carpool_repeating
from amarillo.services.trips import TripStore
from amarillo.services.stops import StopsStore


import logging
logger = logging.getLogger(__name__)

def test_trip_store_put_one_time_carpool():
    trip_store = TripStore(StopsStore())

    t = trip_store.put_carpool(cp1)
    assert t != None
    assert len(t.stop_times) >= 2
    assert t.stop_times[0].stop_id == 'mfdz:12073:001'
    assert t.stop_times[-1].stop_id == 'de:12073:900340137::3'

def test_trip_store_put_repeating_carpool():
    trip_store = TripStore(StopsStore())

    t = trip_store.put_carpool(carpool_repeating)
    assert t != None
    assert len(t.stop_times) >= 2
