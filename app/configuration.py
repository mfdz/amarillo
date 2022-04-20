# separate file so that it can be imported without initializing FastAPI

from app.services import stops
from app.services import trips
from app.services.carpools import CarpoolService

from app.services.config import config

from app.utils.container import container
import app.services.gtfs_generator as gtfs_generator

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
