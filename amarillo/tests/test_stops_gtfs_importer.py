from amarillo.services.stop_importer.gtfs import GtfsStopsImporter


def test_load_stops_from_gtfs_():
    stopsDataFrames = GtfsStopsImporter().load_stops(
        id='test_load_stops_from_gtfs', url='amarillo/tests/fixtures/stops.gtfs.zip'
    )

    assert len(stopsDataFrames) > 0
    assert stopsDataFrames.loc[0, ['x', 'y', 'stop_name', 'id']].values.tolist() == [
        8.75033716398694,
        48.7891850492262,
        'Monakam Brunnenstr.',
        'de:08235:4060:0:3',
    ]
