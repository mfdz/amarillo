import logging.config
import warnings

from amarillo.configuration import configure_services, configure_admin_token
from amarillo.services.config import config

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger("main")

import uvicorn
import mimetypes
from starlette.staticfiles import StaticFiles

from amarillo.routers import carpool, agency, agencyconf, region
from fastapi import FastAPI, Request

# https://pydantic-docs.helpmanual.io/usage/settings/
from amarillo.views import home

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
            "externalDocs": {
                "description": "Find out more about Amarillo - the carpooling intermediary",
                "url": "https://github.com/mfdz/amarillo",
            },
                  }],
              redoc_url=None
)

app.include_router(carpool.router)
app.include_router(agency.router)
app.include_router(agencyconf.router)
app.include_router(region.router)


def configure():
    configure_admin_token()
    configure_services()
    configure_routing()


@app.middleware("http")
async def log_request_data(request: Request, call_next):
    if request.method == "POST" and config.debug:
        body = await request.body()
        logger.info(f"POST Request to {request.url.path} with body: {body.decode('utf-8')}")
    
    return await call_next(request)

def configure_routing():
    mimetypes.add_type('application/x-protobuf', '.pbf')
    app.mount('/static', StaticFiles(directory='static'), name='static')
    if config.publish_deprecated_gtfs_endpoint:
        warnings.warn(
            """
            Publishing gtfs endpoint is deprecated, clients should switch to 
            region/<regionid>/gtfs and region/<regionid>/gtfs-rt. To disable 
            the endpoint set env var publish_deprecated_gtfs_endpoint to TRUE.
            """,
            category=DeprecationWarning,
            stacklevel=2,
        )
        app.mount('/gtfs', StaticFiles(directory='data/gtfs'), name='gtfs')
        
    app.include_router(home.router)


if __name__ == "__main__":
    configure()
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    configure()
