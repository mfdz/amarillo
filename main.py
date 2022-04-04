import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, Response
from typing import List, Dict
from pydantic import (BaseModel, BaseSettings)

from models.Carpool import Carpool
from models.StopTime import StopTime
from services.gtfs import gtfs_rt


# https://pydantic-docs.helpmanual.io/usage/settings/
class Settings(BaseSettings):
    agencies: List[str]


settings = Settings(_env_file='prod.env', _env_file_encoding='utf-8')

print("Hello Amarillo!")

app = FastAPI(title="Amarillo - The Carpooling Intermediary",
              description="This service allows carpool agencies to publish "
                          "their trip offers, so routing services may suggest "
                          "them as trip options. For carpool offers, only the "
                          "minimum required information (origin/destination, "
                          "optionally intermediate stops, departure time and a "
                          "deep link for booking/contacting the driver) needs to "
                          "be published, booking/contact exchange is to be "
                          "handled by the publishing agency.",
              version="0.0.1",
              # TODO 404
              terms_of_service="http://mfdz.de/carpool-hub-terms/",
              contact={
                  # "name": "unused",
                  # "url": "http://unused",
                  "email": "info@mfdz.de",
              },
              license_info={
                  "name": "AGPL-3.0 License",
                  "url": "https://www.gnu.org/licenses/agpl-3.0.de.html",
              },
              openapi_tags=[
                  {
                      "name": "carpool",
                      # "description": "Find out more about Amarillo - the carpooling intermediary",
                      "externalDocs": {
                          "description": "Find out more about Amarillo - the carpooling intermediary",
                          "url": "https://github.com/mfdz/amarillo",
                      },
                  }],
              servers=[
                  {
                      "description": "Demo server by MFDZ",
                      "url": "http://amarillo.mfdz.de:8000"
                  }
              ],
              redoc_url=None
              )

stops0 = [StopTime(id="de:12073:900340137::6", name="qwert", lat=45, lon=10),
          StopTime(id="de:12073:900340137::7", name="dd", lat=45, lon=10)]

cp0 = Carpool(
    id="dieNull",
    agency="a",
    deeplink="https://ride2go.com/trip/123",
    stops=stops0,
    departureTime="15:00",
    departureDate="2022-03-30",
)

data1 = {
    'id': "Eins",
    'agency': "ride2go",
    'deeplink': "https://ride2go.com/trip/123",
    'stops': [
        {'id': "de:12073:900340137::2", 'name': "abc", 'lat': 45, 'lon': 9},
        {'id': "de:12073:900340137::3", 'name': "xyz", 'lat': 45, 'lon': 9}],
    'departureTime': "15:00",
    'departureDate': "2022-03-30",
}

cp1 = Carpool(**data1)

# JSON string for trying out the API in Swagger
cp2 = """
{
  "id": "Vier",
  "agency": "string",
  "deeplink": "http://mfdz.de",
  "stops": [
    {
      "id": "de:12073:900340137::4", "name": "drei", "lat": 45, "lon": 9
    },
    {
      "id": "de:12073:900340137::5", "name": "drei b", "lat": 45, "lon": 9
    }
  ],
  "departureTime": "12:34",
  "departureDate": "2022-03-30",
  "lastUpdated": "2022-03-30 12:34"
}
"""

carpools: Dict[str, Carpool] = {
    cp0.id: cp0,
    cp1.id: cp1
}


@app.put("/carpool",
         operation_id="updatecarpool",
         summary="Update an existing carpool",
         # TODO description="",
         response_model=Carpool,
         description="Carpool object that should be updated",
         status_code=status.HTTP_202_ACCEPTED,
         tags=["carpool"],
         # TODO next to the status codes are "Links". There is nothing shown now.
         # Either show something there, or hide the Links, or do nothing.
         responses={400: {"description": "Invalid"},
                    404: {"description": "Carpool not found"},
                    # TODO note that automatic validations against the schema
                    # are returned with code 422, also shown in Swagger.
                    # maybe 405 is not needed?
                    405: {"description": "Validation exception"}})
async def put_carpool(cp: Carpool):
    exists = carpools.get(cp.id) != None

    if not exists:
        raise HTTPException(status_code=404, detail="Carpool not found")

    if cp.lastUpdated == None:
        cp.lastUpdated = datetime.now()

    carpools[cp.id] = cp

    return cp


@app.post("/carpool",
          tags=["carpool"])
async def post_carpool(cp: Carpool) -> Carpool:
    if cp.lastUpdated == None:
        cp.lastUpdated = datetime.now()

    exists = carpools.get(cp.id) != None

    if exists:
        raise "TODO carpool exist"

    carpools[cp.id] = cp

    return cp


# TODO make use of agencyId 
@app.get("/carpool/{agencyId}/{carpoolId}",
         tags=["carpool"])
async def get_carpool(agencyId: str, carpoolId: str) -> Carpool:
    exists = carpools.get(carpoolId) != None

    if not exists:
        return "TODO carpool does not exist"

    return carpools[carpoolId]


# TODO make use of agencyId     
@app.delete("/carpool/{agencyId}/{carpoolId}",
            tags=["carpool"])
async def delete_carpool(agencyId: str, carpoolId: str):
    exists = carpools.get(carpoolId) != None

    if not exists:
        return "TODO carpool does not exist"

    carpools[carpoolId] = None
    return "TODO success "


@app.get("/gtfs-rt")
async def read_gtfs_rt(format: str = 'protobuf', tags=["gtfs"]):
    data = gtfs_rt(carpools, format)
    if "json" == format.lower():
        return JSONResponse(content=data)
    else:
        return Response(content=data, media_type="application/x-protobuf")


@app.get("/")
async def read_root():
    return {"msg": "Hello Amarillo!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
