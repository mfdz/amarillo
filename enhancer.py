import pyinotify
import json
import time

from app.configuration import configure_enhancer_services
from app.utils.container import container
from app.models.Carpool import Carpool

print("Hello Enhancer")

configure_enhancer_services()


wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.IN_DELETE | pyinotify.IN_CLOSE_WRITE

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        print ("Creating:", event.pathname)

        with open(event.pathname, 'r', encoding='utf-8') as f:
            dict = json.load(f)
            carpool = Carpool(**dict)

        container['carpools'].put(carpool.agency, carpool.id, carpool)
        return

    def process_IN_DELETE(self, event):
        print ("Removing:", event.pathname)


notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
notifier.start()

wdd = wm.add_watch('data/carpool', mask, rec=True)
import time
try:
    for s in range(500):
        print(container['carpools'].get_all_ids())
        time.sleep(1)
finally:
    wm.rm_watch(list(wdd.values()))

    notifier.stop()
