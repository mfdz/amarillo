from datetime import datetime, timedelta

from amarillo.services.importing.noi import NoiImporter

noi_carpool = {
    '_timestamp': '2024-01-11 04:30:00.086+0000',
    'tdescription': 'itinerary_details',
    'tmetadata': {},
    'tname': 'itinerary_details',
    'ttype': 'Instantaneous',
    'tunit': 'json',
    'mperiod': 3600,
    'mtransactiontime': '2024-01-04 04:40:07.072+0000',
    'mvalidtime': '2024-01-11 04:30:00.086+0000',
    'mvalue': {
        'status': 'PUBLISHED',
        'end_post_code': '39021',
        'end_lat_approx': 46.62,
        'end_lon_approx': 10.85,
        'seats_reserved': 0,
        'start_post_code': '39100',
        'ride_distance_km': 56.9,
        'start_lat_approx': 46.49,
        'start_lon_approx': 11.36,
        'ride_start_at_UTC': '2024-01-10T16:30Z',
        'ride_created_at_UTC': '2024-01-03T22:01:18Z',
        'ride_duration_minutes': 54.0,
    },
    'prlineage': 'UMMADUM',
    'prname': 'odh-mobility-dc-carpooling',
    'prversion': 'c50134a38601c73fa33d95533e1329792eafd065',
    'sactive': True,
    'savailable': True,
    'scode': 'cd2beb0dd88ead7a0e16bb41a2221d1d',
    'scoordinate': {'x': 11.36, 'y': 46.49, 'srid': 4326},
    'smetadata': {
        'end_lat_approx': 46.62,
        'end_lon_approx': 10.85,
        'start_lat_approx': 46.49,
        'start_lon_approx': 11.36,
    },
    'sname': 'UMMADUM_1',
    'sorigin': 'UMMADUM',
    'stype': 'CarpoolingTrip',
}


def test_departure_date_is_tomorrow_in_test_mode():
    importer = NoiImporter('ummadum', test_mode=True)
    cp = importer._extract_carpool(noi_carpool)
    assert cp.departureDate == (datetime.now() + timedelta(days=1)).date()


def test_departure_date_is_ok_in_not_test_mode():
    importer = NoiImporter(
        'ummadum',
    )
    cp = importer._extract_carpool(noi_carpool)
    assert cp.departureDate == datetime.fromisoformat('2024-01-10T16:30+00:00').date()
