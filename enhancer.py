import pyinotify
import json
import time
import logging
import logging.config

from app.configuration import configure_enhancer_services
from app.utils.container import container
from app.models.Carpool import Carpool

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger("enhancer")

logger.info("Hello Enhancer")

configure_enhancer_services()

wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.IN_DELETE | pyinotify.IN_CLOSE_WRITE


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        logger.info("Creating: %s", event.pathname)

        with open(event.pathname, 'r', encoding='utf-8') as f:
            dict = json.load(f)
            carpool = Carpool(**dict)

        container['carpools'].put(carpool.agency, carpool.id, carpool)
        return

    def process_IN_DELETE(self, event):
        logger.info("Removing: %s", event.pathname)

notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
notifier.start()

wdd = wm.add_watch('data/carpool', mask, rec=True)
import time

try:
    for s in range(500):
        logger.info(container['carpools'].get_all_ids())
        time.sleep(1)
finally:
    wm.rm_watch(list(wdd.values()))

    notifier.stop()

    logger.info("Goodbye Enhancer")
