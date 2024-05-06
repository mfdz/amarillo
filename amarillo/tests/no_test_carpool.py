from fastapi.testclient import TestClient
from amarillo.main import app
from amarillo.tests.sampledata import carpool_1234, data1

client = TestClient(app)

# TODO FG: This test needs a clean temporary storage folder, not the hard coded data dir.
def test_doc():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
def test_get_mfdz_0():
    response = client.get("/carpool/mfdz/0")
    assert response.status_code == 404
    assert response.json() == {"detail": "Carpool with agency mfdz and id 0 does not exist."}


def test_delete_mfdz_0():
    response = client.delete("/carpool/mfdz/0")
    assert response.status_code == 404
    assert response.json() == {"detail": "Carpool with id 0 does not exist."}


def test_post():
    response = client.get(f"/carpool/mfdz/{data1['id']}")
    assert response.status_code == 404, "The carpool should not exist yet"

    response = client.post("/carpool/", json=data1)
    assert response.status_code == 200, "The first post must work with 200"

    response = client.get(f"/carpool/mfdz/{data1['id']}")
    assert response.status_code == 200, "After post, the get must work"

    response = client.delete(f"/carpool/mfdz/{data1['id']}")
    assert response.status_code == 200, "The first delete must work with 200"

    response = client.delete(f"/carpool/mfdz/{data1['id']}")
    assert response.status_code == 404, "The second delete must fail"
