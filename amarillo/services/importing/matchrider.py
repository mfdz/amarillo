import logging
import json

from amarillo.models.Carpool import StopTime

from .amarillo import AmarilloImporter

logger = logging.getLogger(__name__)

class MobilityDIYImporter(AmarilloImporter):
    def __init__(self, url, http_headers):
        super().__init__('matchrider', url, http_headers)

    @staticmethod
    def _extract_stop(stop):
        stop_id = f'matchrider:{stop["id"]}' if not stop['id'].startswith('matchrider:') else stop['id']
        
        return StopTime(
            id=stop_id,
            name=stop['name'],
            lat=float(stop['lat']),
            lon=float(stop['lon']),
            arrivalTime=stop.get('arrivalTime'),
            departureTime=stop.get('departureTime'),
            pickup_dropoff=stop.get('pickup_dropoff'),
        )

    def _get_data_from_json_response(self, json_response):
        payload = json.loads(json_response.get('Payload'))
        filtered_payload = []
        for cp in payload:
            if cp.get('path') is None:
                logger.warning(f"Offer {cp['id']} has no path, will be ignored" )
                continue
        
            for stop in cp['stops']:
                if 'id' not in stop:
                    logger.warning(f"Offer {cp['id']}'s stop {stop} has no ID, offer will be ignored" )
                    continue
                elif not stop['id'].startswith('matchrider:'):
                    stop['id'] = f'matchrider:{stop["id"]}'

            filtered_payload.append(cp)
        return filtered_payload
