from app.models.gtfs import GtfsTimeDelta, GtfsStopTime
from app.models.Carpool import Carpool, Weekday
from app.services.routing import RoutingService
from shapely.geometry import Point, LineString, box
from datetime import datetime, timedelta, date
import logging

logger = logging.getLogger(__name__)

class Trip:

    def __init__(self, trip_id, route_name, headsign, url, calendar, departureTime, path, agency, lastUpdated, stop_times):
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
        else:
            self.start = datetime.combine(calendar, departureTime)    
            self.runs_regularly = False
            self.weekdays = [0,0,0,0,0,0,0]

        self.start_time = departureTime
        self.path = path   
        self.trip_id = trip_id
        self.url = url
        self.agency = agency
        self.stops = []
        self.lastUpdated = lastUpdated
        self.stop_times = stop_times
        self.bbox = path.bounds
        self.route_name = route_name
        self.trip_headsign = headsign

    def path_as_line_string(self):
        return path
    
    def _total_seconds(self, instant):
        return instant.hour * 3600 + instant.minute * 60 + instant.second

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
        return self.route_name

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

    def __init__(self, stops_store):
        self.transformer = TripTransformer(stops_store)
        self.stops_store = stops_store
        self.trips = {}
        self.deleted_trips = {}
        self.recent_trips = {}


    def put_carpool(self, carpool: Carpool):
        """
        Adds carpool to the TripStore.
        """
        # TODO: check, if already known (id AND lastUpdated matches)
        # Only then we should transform to trip and store

        id = "{}:{}".format(carpool.agency, carpool.id)
        try: 
            # TODO move trip transformation to proper class
            # TODO split enhancement and trip transformation
            trip = self.transformer.transform_to_trip(carpool)
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


class TripTransformer:

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
    router = RoutingService()

    def __init__(self, stops_store):
        self.stops_store = stops_store

    def transform_to_trip(self, carpool):
        (lineString, stop_times, route_name, headsign) = self._enhance_carpool(carpool)
        trip_id = f"{carpool.agency}:{carpool.id}"
        trip = Trip(trip_id, route_name, headsign, str(carpool.deeplink), carpool.departureDate, carpool.departureTime, lineString, carpool.agency, carpool.lastUpdated, stop_times)

        return trip

    def _enhance_carpool(self, carpool):
        path = self._path_for_ride(carpool)
        # If no path has been found: ignore
        if not path.get("time"):
            raise RuntimeError ('No route found.')

        lineString = LineString(path["points"]["coordinates"])
        virtual_stops = self.stops_store.find_additional_stops_around(lineString, carpool.stops) 
        if not virtual_stops.empty:
            virtual_stops["time"] = self._estimate_times(path, virtual_stops['distance'])
            logger.debug("Virtual stops found: {}".format(virtual_stops))

        trip_id = f"{carpool.agency}:{carpool.id}"
        route_name = virtual_stops.iloc(0)[0]["stop_name"] + " nach " + virtual_stops.tail(1).iloc(0)[0]["stop_name"]
        stop_times = self._stops_and_stop_times(carpool.departureTime, trip_id, virtual_stops)
        headsign= virtual_stops.tail(1).iloc(0)[0]["stop_name"]
        
        return (lineString, stop_times, route_name, headsign)

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

    def _stops_and_stop_times(self, start_time, trip_id, stops_frame):
        # Assumptions: 
        # arrival_time = departure_time
        # pickup_type, drop_off_type for origin: = coordinate/none
        # pickup_type, drop_off_type for destination: = none/coordinate
        # timepoint = approximate for origin and destination (not sure what consequences this might have for trip planners)
        number_of_stops = len(stops_frame.index)
        total_distance = stops_frame.iloc[number_of_stops-1]["distance"]
        
        first_stop_time = GtfsTimeDelta(hours = start_time.hour, minutes = start_time.minute, seconds = start_time.second) 
        stop_times = []
        seq_nr = 0
        for i in range(0, number_of_stops):
            current_stop = stops_frame.iloc[i]

            print(current_stop.id, current_stop.time)
            if not current_stop.id:
                continue
            elif i == 0:
                if (stops_frame.iloc[1].time-current_stop.time) < 1000:
                    # skip custom stop if there is an official stop very close by
                    logger.debug("Skipped stop %s", current_stop.id)
                    continue
            else:
                if (current_stop.time-stops_frame.iloc[i-1].time) < 5000 and not i==1:
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
            stop_times.append(GtfsStopTime(
                trip_id, 
                str(next_stop_time), 
                str(next_stop_time), 
                current_stop.id, 
                seq_nr, pickup_type, 
                dropoff_type, 
                self.STOP_TIMES_TIMEPOINT_APPROXIMATE))
        return stop_times
    
    def _is_dropoff_stop(self, current_stop, total_distance):
        return current_stop["distance"] >= 0.5 * total_distance
        
    def _is_pickup_stop(self, current_stop, total_distance):
        return current_stop["distance"] < 0.5 * total_distance

