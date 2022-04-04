import uvicorn
from datetime import date, datetime, time, timedelta
from enum import Enum
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse, Response
from typing import List, Dict, Set, Union, Optional
from pydantic import ( BaseModel, BaseSettings, Field, HttpUrl, NegativeInt,
                       PositiveInt, conint, conlist, constr )
from services.gtfs import gtfs_rt

# https://pydantic-docs.helpmanual.io/usage/settings/
class Settings(BaseSettings):
    agencies: List[str]
   
settings = Settings(_env_file='prod.env', _env_file_encoding='utf-8')

print("Hello Amarillo!")

app = FastAPI(title="Amarillo - The Carpooling Intermediary",
              description="""This service allows carpool agencies to publish their trip offers, so routing services may suggest them as trip options. For carpool offers, only the minimum required information (origin/destination, optionally intermediate stops, departure time and a deep link for booking/contacting the driver) needs to be published, booking/contact exchange is to be handled by the publishing agency.""",
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
                      #"description": "Find out more about Amarillo - the carpooling intermediary",
                      "externalDocs": {
                          "description": "Find out more about Amarillo - the carpooling intermediary",
                          "url": "https://github.com/mfdz/amarillo",
                      },
                  },
                  {
                      "name": "servers",
                      "url": "https://amarillo.mfdz.de:8000"
                  }
              ],
              redoc_url=None
              )

class Weekday(str, Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"

class StopTime(BaseModel):
    id: str = None
    name: str
    arrivalTime: time = None
    departureTime: time = None # in GTFS time can be >24:00
    lat: float = Field(ge=-90, lt=90, multiple_of=1e-10) 
    lon: float = Field(ge=-180, lt=180, multiple_of=1e-10) 
    
class Carpool(BaseModel):
    id: str = Field(min_length=1, max_length=256, regex='^\\w*$') 
    agency: str = Field(..., example="ride2go")
    deeplink: HttpUrl 
    stops: List[StopTime] = Field([], min_items=2, max_items=10,
                                  description="""The first stop is the origin of the trip. The last stop is
                                  the destination of the trip.""") 
    departureTime: time 
    departureDate: Union[date, Set[Weekday]] 
    lastUpdated: Optional[datetime] = None

stops0 = [StopTime(id="adsf", name="qwert", lat=45, lon=10), StopTime(id="sss", name="dd", lat=45, lon=10)]

cp0 = Carpool(
    id="dieNull", 
    agency="a", 
    deeplink="https://ride2go.com/trip/123", 
    stops = stops0,
    departureTime="15:00", 
    departureDate="2022-03-30", 
)

data1 = {
    'id': "Eins",
    'agency': "ride2go",
    'deeplink': "https://ride2go.com/trip/123",
    'stops': [{'id': "asdf", 'name': "qewrt", 'lat':45, 'lon':9},
             {'id': "yy", 'name': "zzz", 'lat':45, 'lon':9}],
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
      "id": "03", "name": "drei", "lat": 45, "lon": 9
    },
    {
      "id": "03b", "name": "drei b", "lat": 45, "lon": 9
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
         summary="Update an existing carpool",
         # TODO description="",
         response_model=Carpool,
         status_code=status.HTTP_202_ACCEPTED,
         tags=["carpool"])
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
    return { "msg": "Hello Amarillo!" }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
