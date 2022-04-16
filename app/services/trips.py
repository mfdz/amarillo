from app.models.gtfs import GtfsTimeDelta, GtfsStopTime
from app.models.Carpool import Carpool, Weekday
from app.services.routing import RoutingService
from shapely.geometry import Point, LineString, box
from datetime import datetime, timedelta, date
import logging

logger = logging.getLogger(__name__)

class Trip:

    NO_BIKES_ALLOWED = 2
    RIDESHARING_ROUTE_TYPE = 1700
    CALENDAR_DATES_EXCEPTION_TYPE_ADDED = 1
    CALENDAR_DATES_EXCEPTION_TYPE_REMOVED = 2
    STOP_TIMES_STOP_TYPE_REGULARLY = 0
    STOP_TIMES_STOP_TYPE_NONE = 1
    STOP_TIMES_STOP_TYPE_PHONE_AGENCY = 2
    STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER = 3
    STOP_TIMES_TIMEPOINT_APPROXIMATE = 0 
    STOP_TIMES_TIMEPOINT_EXACT = 1 

    def __init__(self, trip_id, url, calendar, departureTime, path, agency, lastUpdated):
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
            self.start = datetime.combine(calendar, departureTime)    
            self.runs_regularly = False
            self.weekdays = [0,0,0,0,0,0,0]

        self.start_time = departureTime
        self.path = path
        self.duration = timedelta(milliseconds=path["time"])     
        self.trip_id = trip_id
        self.url = url
        self.agency = agency
        self.stops = []
        self.lastUpdated = lastUpdated


    def path_as_line_string(self):
        return LineString(self.path["points"]["coordinates"])
    
    def _total_seconds(self, instant):
        return instant.hour * 3600 + +instant.minute * 60 + instant.second

    def start_time_str(self):
        return self.start_time.strftime("%H:%M:%S")

    def next_trip_dates(self, start_date, day_count=14):
        if self.runs_regularly:
            for single_date in (start_date + timedelta(n) for n in range(day_count)):
                if self.weekdays[single_date.weekday()]==1:
                    yield single_date.strftime("%Y%m%d")
        else:
            yield self.start.strftime("%Y%m%d")

    def route_long_name(self):
        return self.stops.iloc(0)[0]["stop_name"] + " nach " + self.stops.tail(1).iloc(0)[0]["stop_name"]

    def stops_and_stop_times(self):
        # Assumptions: 
        # arrival_time = departure_time
        # pickup_type, drop_off_type for origin: = coordinate/none
        # pickup_type, drop_off_type for destination: = none/coordinate
        # timepoint = approximate for origin and destination (not sure what consequences this might have for trip planners)
        number_of_stops = len(self.stops.index)
        total_distance = self.stops.iloc[number_of_stops-1]["distance"]
        
        first_stop_time = GtfsTimeDelta(hours = self.start_time.hour, minutes = self.start_time.minute, seconds = self.start_time.second) 
        stop_times = []
        seq_nr = 0
        for i in range(0, number_of_stops):
            current_stop = self.stops.iloc[i]
            if not current_stop.id:
                continue
            elif i == 0:
                if (self.stops.iloc[1].time-current_stop.time) < 1000:
                    # skip custom stop if there is an official stop very close by
                    logger.debug("Skipped stop %s", current_stop.id)
                    continue
            else:
                if (current_stop.time-self.stops.iloc[i-1].time) < 5000:
                    # skip latter stop if it's very close (<5 seconds drive) by the preceding
                    logger.debug("Skipped stop %s", current_stop.id)
                    continue
            
            trip_time = timedelta(milliseconds=int(current_stop.time))
            is_dropoff = self._is_dropoff_stop(current_stop, total_distance)
            is_pickup = self._is_pickup_stop(current_stop, total_distance)
            # TODO would be nice if possible to publish a minimum shared distance 
            pickup_type = self.STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER if is_pickup else self.STOP_TIMES_STOP_TYPE_NONE
            dropoff_type = self.STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER if is_dropoff else self.STOP_TIMES_STOP_TYPE_NONE
            
            next_stop_time = first_stop_time + trip_time
            seq_nr += 1
            yield seq_nr, GtfsStopTime(self.trip_id, str(next_stop_time), str(next_stop_time), current_stop.id, seq_nr, pickup_type, dropoff_type, self.STOP_TIMES_TIMEPOINT_APPROXIMATE)
    
    def _is_dropoff_stop(self, current_stop, total_distance):
        return current_stop["distance"] >= 0.5 * total_distance
        
    def _is_pickup_stop(self, current_stop, total_distance):
        return current_stop["distance"] < 0.5 * total_distance

    def intersects(self, bbox):
        return self.bbox.intersects(box(*bbox))

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
    recent_trips = {}

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
            if carpool.lastUpdated and carpool.lastUpdated.date() >= self._yesterday():
                self.recent_trips[id] = trip
            logger.debug("Added trip %s", id)
            return trip
        except Exception as err:
            logger.error("Failed to add carpool %s to TripStore.", id, exc_info=True)

    def delete_carpool(self, agencyScopedCarpoolId):
        """
            Deletes carpool from the TripStore.
        """
        trip_to_be_deleted = self.trips.get(agencyScopedCarpoolId)
        if trip_to_be_deleted:
            self.deleted_trips[agencyScopedCarpoolId] = trip_to_be_deleted
            del self.trips[agencyScopedCarpoolId]
        
        if self.recent_trips.get(agencyScopedCarpoolId):
            del self.recent_trips[agencyScopedCarpoolId]

        logger.debug("Deleted trip %s", id)

    def purge_trips_older_than(self, day):
        for key in self.recent_trips.keys():
            t = self.recent_trips.get(key)
            if t and t.lastUpdated.date() < day:
                del recent_trips[key]

        for key in self.deleted_trips.keys():
            t = self.deleted_trips.get(key)
            if t and t.lastUpdated.date() < day:
                del deleted_trips[key]

    def _yesterday(self):
        return date.today() - timedelta(days=1)

    def _transform_to_trip(self, carpool):
        bbox, path = self._bbox_and_path_for_ride(carpool)
        # If no path has been found: ignore
        if not path.get("time"):
            raise RuntimeError ('No route found.')

        trip = Trip(f"{carpool.agency}:{carpool.id}", str(carpool.deeplink), carpool.departureDate, carpool.departureTime, path, carpool.agency, carpool.lastUpdated)
        virtual_stops = self.stops_store.find_additional_stops_around(trip.path_as_line_string(), carpool.stops) 
        if not virtual_stops.empty:
            virtual_stops["time"] = self._estimate_times(path, virtual_stops['distance'])
            logger.debug("Virtual stops found: {}".format(virtual_stops))
        
        trip.stops = virtual_stops
        trip.bbox = bbox
        return trip
    
    def _bbox_and_path_for_ride(self, carpool):
        points = self._stop_coords(carpool.stops)
        bbox = (
            min([p.x for p in points]),
            min([p.y for p in points]),
            max([p.x for p in points]),
            max([p.y for p in points])
            )
        return box(*bbox), self.router.path_for_stops(points)
    
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
