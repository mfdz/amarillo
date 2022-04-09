import requests
import logging

logger = logging.getLogger(__name__)

class RoutingService():
    def __init__(self, gh_url = 'https://api.mfdz.de/gh'):
        self.gh_service_url = gh_url

    def path_for_stops(self, points):
    	# Retrieve graphhopper route traversing given points
        directions = self._get_directions(points)
        if directions and len(directions.get("paths"))>0:
            return directions.get("paths")[0] 
        else:
            return {}
	
    def _get_directions(self, points):
        req_url = self._create_url(points, True, True)
        logger.debug("Get directions via: {}".format(req_url))
        response = requests.get(req_url)
        status = response.status_code
        if status == 200:
            # Found route between points
            return response.json()
        else:
            try:    
            	logger.error("Get directions failed: %s", response.json().get('message'))
            except:
            	logger.error("Get directions failed with status code %s", status)

    def _create_url(self, points, calc_points = False, instructions = False):
        """ Creates GH request URL """
        locations = ""
        for point in points:
            locations += "point={0}%2C{1}&".format(point.y, point.x)
            
        return "{0}/route?{1}instructions={2}&calc_points={3}&points_encoded=false".format(
            self.gh_service_url, locations, instructions, calc_points)    
