# separate file so that it can be imported without initializing FastAPI
from amarillo.utils.container import container
import logging

from amarillo.services.agencyconf import AgencyConfService, agency_conf_directory
from amarillo.services.agencies import AgencyService
from amarillo.services.regions import RegionService

from amarillo.services.config import config

from amarillo.utils.utils import assert_folder_exists

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

def configure_admin_token():
    if config.admin_token is None:
        message = "ADMIN_TOKEN environment variable not set"
        logger.error(message)
        raise Exception(message)

    logger.info("ADMIN_TOKEN environment variable found")
    # Note: the admin token is not persisted. When needed it is accessed
    # via config.admin_token as above
