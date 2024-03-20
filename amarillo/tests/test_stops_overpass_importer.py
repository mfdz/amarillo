from amarillo.services.stop_importer.overpass import OverpassStopsImporter


def test_load_geojson_stops_from_web_():
    with open('amarillo/tests/fixtures/stops_overpass_result.csv') as f:
        stopsDataFrames = OverpassStopsImporter()._parse_overpass_csv_response(f)

    assert len(stopsDataFrames) > 0
    assert stopsDataFrames.loc[0, ['x', 'y', 'stop_name', 'id']].values.tolist() == [
        11.7621206,
        46.7470278,
        'P+R',
        'osm:n5206558994',
    ]
