from amarillo.tests.sampledata import carpool_with_unchanged_stops, stops_1234
from amarillo.services.trips import TripTransformer
from amarillo.services.stops import StopsStore
from amarillo.services.agencyconf import AgencyConfService


def test_transform_carpool_with_unchanged_stops():
    trip_transformer = TripTransformer(StopsStore(), AgencyConfService())

    t = trip_transformer.enhance_carpool(carpool_with_unchanged_stops.model_copy(deep=True))
    assert t != None
    assert len(t.stops) == len(carpool_with_unchanged_stops.stops)
    for i in range(0, len(t.stops)):
        assert t.stops[i].id == carpool_with_unchanged_stops.stops[i].id
        assert t.stops[0].pickup_dropoff == 'pickup_and_dropoff'

