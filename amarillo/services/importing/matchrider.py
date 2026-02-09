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
        if stop['id'].startswith('matchrider:'):
            stop_id = stop['id']
        else:
            # if stop id does not start with matchrider:, 
            # we expect ifopt. However, only station ifopt 
            # is currently supported, so we chop off trailing parts
            stop_id = stop['id'][0:stop['id'].find(':',9)]
        stop_name = stop.get('name','-')
        arrivalTime = stop.get('arrivalTime')
        departureTime = stop.get('departureTime')
        if arrivalTime is not None and len(arrivalTime)==5:
            arrivalTime = arrivalTime+":00"
        if departureTime is not None and len(departureTime)==5:
            departureTime = departureTime+":00"

        return StopTime(
            id=stop_id,
            name=stop_name,
            lat=float(stop['lat']),
            lon=float(stop['lon']),
            arrivalTime=arrivalTime,
            departureTime=departureTime,
            pickup_dropoff=stop.get('pickup_dropoff'),
        )

    def _should_offer_be_ignored(self, cp):
        if cp.get('path') is None:
            logger.warning(f"Offer {cp['id']} has no path, will be ignored" )
            return True
    
        for stop in cp['stops']:
            if 'id' not in stop:
                logger.warning(f"Offer {cp['id']}'s stop {stop} has no ID, offer will be ignored" )
                return True
    
        return False

    def _get_data_from_json_response(self, json_response):
        payload = json.loads(json_response.get('Payload'))
        filtered_payload = []
        for cp in payload:
            if self._should_offer_be_ignored(cp):
                continue
            
            filtered_payload.append(cp)
        return filtered_payload
