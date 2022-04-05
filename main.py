import uvicorn

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, Response
from typing import List
from pydantic import (BaseSettings)

from models.Carpool import Carpool
from models.StopTime import StopTime
import routers.carpool
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
                  },
                  {
                      "description": "Localhost for development",
                      "url": "http://localhost:8000"
                  }
              ],
              redoc_url=None
              )

app.include_router(routers.carpool.router)

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
