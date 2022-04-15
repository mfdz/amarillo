from fastapi.testclient import TestClient
from app.main import app, configure_services
from app.tests.sampledata import carpool_1234, data1, carpool_repeating_json
from app.services.gtfs_export import GtfsExport
from app.services.gtfs import GtfsRtProducer
from app.services.stops import StopsStore
from app.services.trips import TripStore
from app.utils.container import container

from datetime import datetime
import time
import pytest

client = TestClient(app)

def test_gtfs_generation():
    response = client.post("/carpool/", json=data1)
    assert response.status_code == 200, "Adding a carpool must work"

    exporter = GtfsExport(None, None, container['trips_store'], container['stops_store'])
    exporter.export('target/tests/test_gtfs_generation/test.gtfs.zip', "target/tests/test_gtfs_generation")

class TestTripConverter:

    def setup_method(self, method):
        configure_services()      

    def test_as_one_time_trip_as_delete_update(self):
        response = client.post("/carpool/", json=data1)
        assert response.status_code == 200, "Adding a carpool must work"
        trip = next(iter(container['trips_store'].trips.values()))

        converter = GtfsRtProducer(container['trips_store'])
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
        response = client.post("/carpool/", json=data1)
        assert response.status_code == 200, "Adding a carpool must work"
        trip = next(iter(container['trips_store'].trips.values()))

        converter = GtfsRtProducer(container['trips_store'])
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
                'route_type': 1700
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
        response = client.post("/carpool/", json=carpool_repeating_json)
        assert response.status_code == 200, "Adding a carpool must work"
        trip = next(iter(container['trips_store'].trips.values()))

        converter = GtfsRtProducer(container['trips_store'])
        json = converter._as_delete_updates(trip, datetime(2022,4,11))

        assert json == [{
                'trip': {
                  'tripId': 'mfdz:Eins', 
                  'startTime': '15:00:00',
                  'startDate': '20220411', 
                  'scheduleRelationship': 'CANCELED', 
                  'routeId': 'mfdz:Eins'
                }
            },
            {
                'trip': {
                  'tripId': 'mfdz:Eins', 
                  'startTime': '15:00:00',
                  'startDate': '20220418', 
                  'scheduleRelationship': 'CANCELED', 
                  'routeId': 'mfdz:Eins'
                }
            }
        ]