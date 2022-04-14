import uvicorn
from starlette.staticfiles import StaticFiles

from app.routers import carpool, gtfs_rt
from fastapi import FastAPI, status
from app.services import stops
from app.services import trips
from app.services.carpools import CarpoolService

from app.services.config import config

from app.utils.container import container
import app.services.gtfs_generator as gtfs_generator

# https://pydantic-docs.helpmanual.io/usage/settings/
from app.views import home

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

app.include_router(carpool.router)
app.include_router(gtfs_rt.router)


def configure():
    configure_services()
    configure_routing()


def configure_routing():
    app.mount('/static', StaticFiles(directory='static'), name='static')
    app.mount('/gtfs', StaticFiles(directory='gtfs'), name='gtfs')
    app.include_router(home.router)


def configure_services():
    stop_sources = [
        {"url": "https://data.mfdz.de/mfdz/stops/custom.csv", "vicinity": 50},
        {"url": "https://data.mfdz.de/mfdz/stops/stops_zhv.csv", "vicinity": 50},
        {"url": "https://data.mfdz.de/mfdz/stops/parkings_osm.csv", "vicinity": 500}
    ]
    stop_store = stops.StopsStore()
    if config.env == 'PROD':
        for stops_source in stop_sources:
            stop_store.register_stops(stops_source["url"], stops_source["vicinity"])
    container['stops_store'] = stop_store
    container['trips_store'] = trips.TripStore(stop_store)
    container['carpools'] = CarpoolService(container['trips_store'])

    if config.env == 'PROD':
        gtfs_generator.start_schedule()


if __name__ == "__main__":
    configure()
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    configure()
