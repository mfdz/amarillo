import json
import time
import logging
import logging.config
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.configuration import configure_enhancer_services
from app.utils.container import container
from app.models.Carpool import Carpool
from app.utils.utils import agency_carpool_ids_from_filename

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger("enhancer")

logger.info("Hello Enhancer")

configure_enhancer_services()

observer = Observer()  # Watch Manager


class EventHandler(FileSystemEventHandler):
    # TODO FG HB should watch for both carpools and agencies
    # in data/agency, data/agencyconf, see AgencyConfService

    def on_closed(self, event):
  
        logger.info("CLOSE_WRITE: Created %s", event.src_path)
        try:
            with open(event.src_path, 'r', encoding='utf-8') as f:
                dict = json.load(f)
                carpool = Carpool(**dict)

            container['carpools'].put(carpool.agency, carpool.id, carpool)
        except FileNotFoundError as e:
            logger.error("Carpool could not be added, as already deleted (%s)", event.src_path)
        except:
            logger.exception("Eventhandler on_closed encountered exception")        

    def on_deleted(self, event):
        try:
            logger.info("DELETE: Removing %s", event.src_path)
            (agency_id, carpool_id) = agency_carpool_ids_from_filename(event.src_path)
            container['carpools'].delete(agency_id, carpool_id)
        except:
            logger.exception("Eventhandler on_deleted encountered exception")


observer.schedule(EventHandler(), 'data/carpool', recursive=True)
observer.start()

import time

try:
    # TODO FG Is this really needed?
    cnt = 0
    ENHANCER_LOG_INTERVAL_IN_S = 600
    while True:
        if cnt == ENHANCER_LOG_INTERVAL_IN_S:
            logger.debug("Currently stored carpool ids: %s", container['carpools'].get_all_ids())
            cnt = 0

        time.sleep(1)
        cnt += 1
finally:
    observer.stop()
    observer.join()

    logger.info("Goodbye Enhancer")
