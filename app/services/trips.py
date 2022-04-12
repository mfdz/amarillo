
from app.models.Carpool import Carpool, Weekday
from app.services.routing import RoutingService
from shapely.geometry import Point, LineString
import datetime
import logging

logger = logging.getLogger(__name__)

class Trip:
    stops= []

    def __init__(self, trip_id, url, calendar, departureTime, path, agency):
        if isinstance(calendar, set):
            self.runs_regularly = True
            self.weekdays = [ 
                1 if Weekday.monday in calendar else 0,
                1 if Weekday.tuesday in calendar else 0,
                1 if Weekday.wednesday in calendar else 0,
                1 if Weekday.thursday in calendar else 0,
                1 if Weekday.friday in calendar else 0,
                1 if Weekday.saturday in calendar else 0,
                1 if Weekday.sunday in calendar else 0,
            ]
            start_in_day = self._total_seconds(departureTime)
            # TODO
            # self.starts = [weekday * 24 * 3600 + start_in_day for weekday in calendar.weekdays] 
        else:
            self.start = datetime.datetime.combine(calendar, departureTime)    
            self.runs_regularly = False
            self.weekdays = [0,0,0,0,0,0,0]

        self.start_time = departureTime
        self.path = path
        self.duration = datetime.timedelta(milliseconds=path["time"])     
        self.trip_id = trip_id
        self.url = url
        self.agency = agency

    def path_as_line_string(self):
        return LineString(self.path["points"]["coordinates"])
    
    def _total_seconds(self, instant):
        return instant.hour * 3600 + +instant.minute * 60 + instant.second

class TripStore():
    """
    TripStore maintains the currently valid trips. A trip is a
    carpool offer enhanced with all stops this 

    Attributes:
        trips           Dict of currently valid trips.
        deleted_trips   Dict of recently deleted trips.
    """
    trips = {}
    deleted_trips = {}

    def __init__(self, stops_store):
        self.router = RoutingService()
        self.stops_store = stops_store

    def put_carpool(self, carpool: Carpool):
        """
        Adds carpool to the TripStore.
        """
        id = "{}:{}".format(carpool.agency, carpool.id)
        try: 
            trip = self._transform_to_trip(carpool)
            self.trips[id] = trip
            logger.debug("Added trip %s", id)
            return trip
        except Exception as err:
            logger.error("Failed to add carpool %s to TripStore.", id, exc_info=True)

    def delete_carpool(self, agencyScopedCarpoolId):
        """
            Deletes carpool from the TripStore.
        """
        trip_to_be_deleted = self.trips[agencyScopedCarpoolId]
        if trip_to_be_deleted:
            self.deleted_trips[agencyScopedCarpoolId] = trip_to_be_deleted
        del self.trips[agencyScopedCarpoolId]
        logger.debug("Deleted trip %s", id)

    def _transform_to_trip(self, carpool):
        path = self._path_for_ride(carpool)
        # If no path has been found: ignore
        if not path.get("time"):
            raise RuntimeError ('No route found.')

        trip = Trip(id, carpool.deeplink, carpool.departureDate, carpool.departureTime, path, carpool.agency)
        virtual_stops = self.stops_store.find_additional_stops_around(trip.path_as_line_string(), carpool.stops) 
        if not virtual_stops.empty:
            virtual_stops["time"] = self._estimate_times(path, virtual_stops['distance'])
            logger.debug("Virtual stops found: {}".format(virtual_stops))
        
        trip.stops = virtual_stops
        return trip
    
    def _path_for_ride(self, carpool):
        points = self._stop_coords(carpool.stops)
        return self.router.path_for_stops(points)
    
    def _stop_coords(self, stops):
        # Retrieve coordinates of all officially announced stops (start, intermediate, target)
        return [Point(stop.lon, stop.lat) for stop in stops]

    def _estimate_times(self, path, distances_from_start):
        cumulated_distance = 0
        cumulated_time = 0
        stop_times = []
        instructions = path["instructions"]

        cnt = 0
        instr_distance = instructions[cnt]["distance"]
        instr_time = instructions[cnt]["time"]

        for distance in distances_from_start:       
            while cnt < len(instructions) and cumulated_distance + instructions[cnt]["distance"] < distance:
                cumulated_distance = cumulated_distance + instructions[cnt]["distance"]
                cumulated_time = cumulated_time + instructions[cnt]["time"]
                cnt = cnt + 1
            
            if cnt < len(instructions):
                percent_dist = (distance - cumulated_distance) / instructions[cnt]["distance"]
                stop_time = cumulated_time + percent_dist * instructions[cnt]["time"]
                stop_times.append(stop_time)
            else:
                logger.warning("distance {} exceeds total length {}, using max arrival time {}".format(distance, cumulated_distance, cumulated_time))
                stop_times.append(cumulated_time)
        return stop_times

