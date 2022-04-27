import logging
import logging.config
from app.configuration import configure_services, configure_admin_token

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger("main")

import uvicorn
import mimetypes
from starlette.staticfiles import StaticFiles

from app.routers import carpool, agency, token
from fastapi import FastAPI, status
from app.services import stops
from app.services import trips
from app.services.carpools import CarpoolService

from app.services.config import config

from app.utils.container import container
import app.services.gtfs_generator as gtfs_generator

# https://pydantic-docs.helpmanual.io/usage/settings/
from app.views import home

logger.info("Hello Amarillo!")

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
                      "description": "Dev server for development",
                      "url": "http://amarillo.mfdz.de:8001"
                  },
                  {
                      "description": "Localhost for development",
                      "url": "http://localhost:8000"
                  }
              ],
              redoc_url=None
              )

app.include_router(carpool.router)
app.include_router(agency.router)
app.include_router(token.router)


def configure():
    configure_admin_token()
    configure_services()
    configure_routing()


def configure_routing():
    mimetypes.add_type('application/x-protobuf', '.pbf')
    app.mount('/static', StaticFiles(directory='static'), name='static')
    app.mount('/gtfs', StaticFiles(directory='data/gtfs'), name='gtfs')
    app.include_router(home.router)


if __name__ == "__main__":
    configure()
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    configure()
