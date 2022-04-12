from fastapi.testclient import TestClient
from app.main import app
from app.tests.sampledata import carpool_1234, data1

client = TestClient(app)


def test_gtfs_rt():
    response = client.get(f"/gtfs-rt?format=json")
    assert response.status_code == 200, "GTFS-RT call worked"
    