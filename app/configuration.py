# separate file so that it can be imported without initializing FastAPI
from app.utils.container import container
import json
import logging
from glob import glob

from app.models.Carpool import Agency, Carpool, Region
from app.services import stops
from app.services import trips
from app.services.agencyconf import AgencyConfService, agency_conf_directory
from app.services.carpools import CarpoolService
from app.services.agencies import AgencyService
from app.services.regions import RegionService

from app.services.config import config

from app.utils.utils import assert_folder_exists
import app.services.gtfs_generator as gtfs_generator

logger = logging.getLogger(__name__)


def create_required_directories():
    logger.info("Checking that necessary directories exist")
    # Folder to serve GTFS(-RT) from
    assert_folder_exists('data/gtfs')
    # Temp folder for GTFS generation
    assert_folder_exists('data/tmp')

    for agency_id in container['agencies'].agencies:
        for subdir in ['carpool', 'trash', 'enhanced', 'failed']:
            foldername = f'data/{subdir}/{agency_id}'
            logger.debug("Checking that necessary %s exist", foldername)
            assert_folder_exists(f'data/{subdir}/{agency_id}')

    # Agency configurations
    assert_folder_exists(agency_conf_directory)


def configure_services():
    container['agencyconf'] = AgencyConfService()
    logger.info("Loaded %d agency configuration(s)", len(container['agencyconf'].agency_id_to_agency_conf))

    container['agencies'] = AgencyService()
    logger.info("Loaded %d agencies", len(container['agencies'].agencies))
    
    container['regions'] = RegionService()
    logger.info("Loaded %d regions", len(container['regions'].regions))

    create_required_directories()


def configure_enhancer_services():
    configure_services()

    logger.info("Load stops...")
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

    logger.info("Restore carpools...")

    for agency_id in container['agencies'].agencies:
        for carpool_file_name in glob(f'data/carpool/{agency_id}/*.json'):
            with open(carpool_file_name) as carpool_file:
                carpool = Carpool(**(json.load(carpool_file)))
                container['carpools'].put(carpool.agency, carpool.id, carpool)
        # notify carpool about carpools in trash, as delete notifications must be sent
        for carpool_file_name in glob(f'data/trash/{agency_id}/*.json'):
            with open(carpool_file_name) as carpool_file:
                carpool = Carpool(**(json.load(carpool_file)))
                container['carpools'].delete(carpool.agency, carpool.id)

    logger.info("Restored carpools: %s", container['carpools'].get_all_ids())

    if config.env == 'PROD':
        logger.info("Starting scheduler")
        gtfs_generator.start_schedule()


def configure_admin_token():
    if config.admin_token is None:
        message = "ADMIN_TOKEN environment variable not set"
        logger.error(message)
        raise Exception(message)

    logger.info("ADMIN_TOKEN environment variable found")
    # Note: the admin token is not persisted. When needed it is accessed
    # via config.admin_token as above
