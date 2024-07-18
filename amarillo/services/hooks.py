from typing import List
from amarillo.models.Carpool import Carpool

class CarpoolEvents:
    def on_create(cp : Carpool):
        pass
    def on_update(cp : Carpool):
        pass
    def on_delete(cp : Carpool):
        pass

carpool_event_listeners : List[CarpoolEvents] = []

def register_carpool_event_listener(cpe : CarpoolEvents):
    carpool_event_listeners.append(cpe)

def run_on_create(cp: Carpool):
    for cpe in carpool_event_listeners:
        cpe.on_create(cp)

def run_on_update(cp: Carpool):
    for cpe in carpool_event_listeners:
        cpe.on_update(cp)

def run_on_delete(cp: Carpool):
    for cpe in carpool_event_listeners:
        cpe.on_delete(cp)