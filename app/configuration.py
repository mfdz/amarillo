# separate file so that it can be imported without initializing FastAPI
import json
import logging
from glob import glob

from app.models.Carpool import Agency, Carpool
from app.services import stops
from app.services import trips
from app.services.carpools import CarpoolService

from app.services.config import config

from app.utils.container import container
from app.utils.utils import assert_folder_exists
import app.services.gtfs_generator as gtfs_generator

logger = logging.getLogger(__name__)

def create_required_directories():
    logger.info("Checking that necessary directories exist")
    # Folder to serve GTFS(-RT) from
    assert_folder_exists('data/gtfs')
    # Temp folder for GTFS generation
    assert_folder_exists('data/tmp')
    for agency_id in container['carpools'].agencies:
        for subdir in ['carpool','trash','enhanced', 'failed']:
            foldername = f'data/{subdir}/{agency_id}'
            logger.debug("Checking that necessary %s exist", foldername)
            assert_folder_exists(f'data/{subdir}/{agency_id}')

def configure_enhancer_services():
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

    # TODO FG: why **? do we expect to store agencies in subdirectories?
    for carpool_file_name in glob('conf/agency/**/*.json'):
        with open(carpool_file_name) as carpool_file:
            agency = Agency(**(json.load(carpool_file)))
            container['carpools'].agencies[agency.id] = agency

    print(f"Loaded agencies: {len(container['carpools'].agencies)}")
    
    create_required_directories()

    for agency_id in container['carpools'].agencies:
        for carpool_file_name in glob(f'data/carpool/{agency_id}/*.json'):
            with open(carpool_file_name) as carpool_file:
                carpool = Carpool(**(json.load(carpool_file)))
                container['carpools'].put(carpool.agency, carpool.id, carpool)
        # notify carpool about carpools in trash, as delete notifications must be sent
        for carpool_file_name in glob(f'data/trash/{agency_id}/*.json'):
            with open(carpool_file_name) as carpool_file:
                carpool = Carpool(**(json.load(carpool_file)))
                container['carpools'].delete(carpool.agency, carpool.id)

    print(f"Loaded carpools: {container['carpools'].get_all_ids()}")

    if config.env == 'PROD':
        gtfs_generator.start_schedule()


def configure_services():
    pass