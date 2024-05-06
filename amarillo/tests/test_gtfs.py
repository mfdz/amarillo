from amarillo.tests.sampledata import carpool_1234, data1, carpool_repeating_json, stop_issue
from amarillo.services.gtfs_export import GtfsExport
from amarillo.services.gtfs import GtfsRtProducer
from amarillo.services.stops import StopsStore
from amarillo.services.trips import TripStore
from amarillo.models.Carpool import Carpool
from datetime import datetime
import time
import pytest


def test_gtfs_generation():
    cp = Carpool(**data1)
    stops_store = StopsStore()
    trips_store = TripStore(stops_store)
    trips_store.put_carpool(cp)

    exporter = GtfsExport(None, None, trips_store, stops_store)
    exporter.export('target/tests/test_gtfs_generation/test.gtfs.zip', "target/tests/test_gtfs_generation")

def test_correct_stops():
    cp = Carpool(**stop_issue)
    stops_store = StopsStore([{"url": "https://datahub.bbnavi.de/export/rideshare_points.geojson", "vicinity": 250}])
    stops_store.load_stop_sources()
    trips_store = TripStore(stops_store)
    trips_store.put_carpool(cp)
    assert len(trips_store.trips) == 1


class TestTripConverter:

    def setup_method(self, method):
        self.stops_store = StopsStore([{"url": "https://datahub.bbnavi.de/export/rideshare_points.geojson", "vicinity": 50}])
        self.trips_store = TripStore(self.stops_store)    

    def test_as_one_time_trip_as_delete_update(self):
        cp = Carpool(**data1)
        self.trips_store.put_carpool(cp)
        trip = next(iter(self.trips_store.trips.values()))
        
        converter = GtfsRtProducer(self.trips_store)
        json = converter._as_delete_updates(trip, datetime(2022,4,11))

        assert json == [{
            'trip': {
              'tripId': 'mfdz:Eins', 
              'startTime': '23:59:00',
              'startDate': '20220530', 
              'scheduleRelationship': 'CANCELED', 
              'routeId': 'mfdz:Eins'
            }
        }]

    def test_as_one_time_trip_as_added_update(self):
        cp = Carpool(**data1)
        self.trips_store.put_carpool(cp)
        trip = next(iter(self.trips_store.trips.values()))
        
        converter = GtfsRtProducer(self.trips_store)
        json = converter._as_added_updates(trip, datetime(2022,4,11))
        assert json == [{
            'trip': {
              'tripId': 'mfdz:Eins', 
              'startTime': '23:59:00',
              'startDate': '20220530', 
              'scheduleRelationship': 'ADDED', 
              'routeId': 'mfdz:Eins',
              '[transit_realtime.trip_descriptor]': { 
                'routeUrl' : 'https://mfdz.de/trip/123',
                'agencyId' : 'mfdz',
                'route_long_name' : 'abc nach xyz',
                'route_type': 1551
                }
            },
            'stopTimeUpdate': [{
                  'stopSequence': 1, 
                  'arrival': {
                    'time': time.mktime(datetime(2022,5,30,23,59,0).timetuple()),
                    'uncertainty': 600
                  },
                  'departure': {
                    'time': time.mktime(datetime(2022,5,30,23,59,0).timetuple()),
                    'uncertainty': 600
                  }, 
                  'stopId': 'mfdz:12073:001', 
                  'scheduleRelationship': 'SCHEDULED',
                  'stop_time_properties': {
                    '[transit_realtime.stop_time_properties]': {
                      'dropoffType': 'NONE',
                      'pickupType': 'COORDINATE_WITH_DRIVER'
                    }
                  }
                },
                { 
                  'stopSequence': 2, 
                  'arrival': {
                    'time': time.mktime(datetime(2022,5,31,0,16,45,0).timetuple()),
                    'uncertainty': 600
                  }, 
                  'departure': {
                    'time': time.mktime(datetime(2022,5,31,0,16,45,0).timetuple()),
                    'uncertainty': 600
                  }, 

                  'stopId': 'de:12073:900340137::3', 
                  'scheduleRelationship': 'SCHEDULED',
                  'stop_time_properties': {
                    '[transit_realtime.stop_time_properties]': {
                      'dropoffType': 'COORDINATE_WITH_DRIVER',
                      'pickupType': 'NONE'
                    }
                  }
                }]
        }]

    def test_as_periodic_trip_as_delete_update(self):
        cp = Carpool(**carpool_repeating_json)
        self.trips_store.put_carpool(cp)
        trip = next(iter(self.trips_store.trips.values()))
        
        converter = GtfsRtProducer(self.trips_store)
        json = converter._as_delete_updates(trip, datetime(2022,4,11))

        assert json == [{
                'trip': {
                  'tripId': 'mfdz:Zwei', 
                  'startTime': '15:00:00',
                  'startDate': '20220411', 
                  'scheduleRelationship': 'CANCELED', 
                  'routeId': 'mfdz:Zwei'
                }
            },
            {
                'trip': {
                  'tripId': 'mfdz:Zwei', 
                  'startTime': '15:00:00',
                  'startDate': '20220418', 
                  'scheduleRelationship': 'CANCELED', 
                  'routeId': 'mfdz:Zwei'
                }
            }
        ]