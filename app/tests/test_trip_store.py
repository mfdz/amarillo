from app.tests.sampledata import cp1, carpool_repeating
import app.services.trips as trips

import logging
logger = logging.getLogger(__name__)

def test_trip_store_put_one_time_carpool():
    trip_store = trips.TripStore()

    t = trip_store.put_carpool(cp1)
    assert t != None
    assert len(t.stops) >= 2


def test_trip_store_put_repeating_carpool():
    trip_store = trips.TripStore()

    t = trip_store.put_carpool(carpool_repeating)
    assert t != None
    assert len(t.stops) >= 2