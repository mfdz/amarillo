from app.models.gtfs import GtfsTimeDelta, GtfsStopTime
from app.models.Carpool import MAX_STOPS_PER_TRIP, Carpool, Weekday, StopTime, PickupDropoffType
from app.services.gtfs_constants import *
from app.services.routing import RoutingService, RoutingException
from app.services.stops import is_carpooling_stop
from app.utils.utils import assert_folder_exists, is_older_than_days, yesterday, geodesic_distance_in_m
from shapely.geometry import Point, LineString, box
from geojson_pydantic.geometries import LineString as GeoJSONLineString
from datetime import datetime, timedelta
import numpy as np
import os
import json
import logging

logger = logging.getLogger(__name__)

class Trip:

    def __init__(self, trip_id, route_name, headsign, url, calendar, departureTime, path, agency, lastUpdated, stop_times, bbox):
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
        self.bbox = bbox
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
        id = "{}:{}".format(carpool.agency, carpool.id)
        filename = f'data/enhanced/{carpool.agency}/{carpool.id}.json'
        try:
            existing_carpool = self._load_carpool_if_exists(carpool.agency, carpool.id)
            if existing_carpool and existing_carpool.lastUpdated == carpool.lastUpdated:
                enhanced_carpool = existing_carpool
            else:
                if len(carpool.stops) < 2 or self.distance_in_m(carpool) < 1000:
                    logger.warning("Failed to add carpool %s:%s to TripStore, distance too low", carpool.agency, carpool.id)
                    self.handle_failed_carpool_enhancement(carpool)
                    return
                enhanced_carpool = self.transformer.enhance_carpool(carpool)
                # TODO should only store enhanced_carpool, if it has 2 or more stops
                assert_folder_exists(f'data/enhanced/{carpool.agency}/')
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(enhanced_carpool.json())
                logger.info("Added enhanced carpool %s:%s", carpool.agency, carpool.id)
            
            return self._load_as_trip(enhanced_carpool)
        except RoutingException as err:
            logger.warning("Failed to add carpool %s:%s to TripStore due to RoutingException %s", carpool.agency, carpool.id, getattr(err, 'message', repr(err)))
            self.handle_failed_carpool_enhancement(carpool)
        except Exception as err:
            logger.error("Failed to add carpool %s:%s to TripStore.", carpool.agency, carpool.id, exc_info=True)
            self.handle_failed_carpool_enhancement(carpool)

    def handle_failed_carpool_enhancement(sellf, carpool: Carpool):
        assert_folder_exists(f'data/failed/{carpool.agency}/')
        with open(f'data/failed/{carpool.agency}/{carpool.id}.json', 'w', encoding='utf-8') as f:
            f.write(carpool.json())

    def distance_in_m(self, carpool):
        if len(carpool.stops) < 2:
            return 0
        s1 = carpool.stops[0]
        s2 = carpool.stops[-1]
        return geodesic_distance_in_m((s1.lon, s1.lat),(s2.lon, s2.lat)) 

    def recently_added_trips(self):
        return list(self.recent_trips.values())

    def recently_deleted_trips(self):
        return list(self.deleted_trips.values())

    def _load_carpool_if_exists(self, agency_id: str, carpool_id: str):
        if carpool_exists(agency_id, carpool_id, 'data/enhanced'):
            try:
                return load_carpool(agency_id, carpool_id, 'data/enhanced')
            except Exception as e:
                # An error on restore could be caused by model changes, 
                # in such a case, it need's to be recreated
                logger.warning("Could not restore enhanced trip %s:%s, reason: %s", agency_id, carpool_id, repr(e))

        return None

    def _load_as_trip(self, carpool: Carpool):
        trip = self.transformer.transform_to_trip(carpool)
        id = trip.trip_id
        self.trips[id] = trip
        if not is_older_than_days(carpool.lastUpdated, 1):
            self.recent_trips[id] = trip
        logger.debug("Added trip %s", id)

        return trip

    def delete_carpool(self, agency_id: str, carpool_id: str):
        """
            Deletes carpool from the TripStore.
        """
        agencyScopedCarpoolId = f"{agency_id}:{carpool_id}"
        trip_to_be_deleted = self.trips.get(agencyScopedCarpoolId)
        if trip_to_be_deleted:
            self.deleted_trips[agencyScopedCarpoolId] = trip_to_be_deleted
            del self.trips[agencyScopedCarpoolId]
        
        if self.recent_trips.get(agencyScopedCarpoolId):
            del self.recent_trips[agencyScopedCarpoolId]

        if carpool_exists(agency_id, carpool_id):
            remove_carpool_file(agency_id, carpool_id)
            
        logger.debug("Deleted trip %s", id)

    def unflag_unrecent_updates(self):
        """
        Trips that were last updated before yesterday, are not recent
        any longer. As no updates need to be sent for them any longer,
        they will be removed from recent recent_trips and deleted_trips.
        """
        for key in list(self.recent_trips):
            t = self.recent_trips.get(key)
            if t and t.lastUpdated.date() < yesterday():
                del self.recent_trips[key]

        for key in list(self.deleted_trips):
            t = self.deleted_trips.get(key)
            if t and t.lastUpdated.date() < yesterday():
                del self.deleted_trips[key]


class TripTransformer:
    REPLACE_CARPOOL_STOPS_BY_CLOSEST_TRANSIT_STOPS = True
    REPLACEMENT_STOPS_SERACH_RADIUS_IN_M = 1000
    SIMPLIFY_TOLERANCE = 0.0001

    router = RoutingService()

    def __init__(self, stops_store):
        self.stops_store = stops_store

    def transform_to_trip(self, carpool):
        stop_times = self._convert_stop_times(carpool)
        route_name = carpool.stops[0].name + " nach " + carpool.stops[-1].name
        headsign= carpool.stops[-1].name
        trip_id = self._trip_id(carpool)
        path = carpool.path
        bbox = box(
            min([pt[0] for pt in path.coordinates]),
            min([pt[1] for pt in path.coordinates]),
            max([pt[0] for pt in path.coordinates]),
            max([pt[1] for pt in path.coordinates]))
            
        trip = Trip(trip_id, route_name, headsign, str(carpool.deeplink), carpool.departureDate, carpool.departureTime, carpool.path, carpool.agency, carpool.lastUpdated, stop_times, bbox)

        return trip

    def _trip_id(self, carpool):
        return f"{carpool.agency}:{carpool.id}"

    def _replace_stops_by_transit_stops(self, carpool, max_search_distance):
        new_stops = []
        for carpool_stop in carpool.stops:
            new_stops.append(self.stops_store.find_closest_stop(carpool_stop, max_search_distance))
        return new_stops

    def enhance_carpool(self, carpool):
        if self.REPLACE_CARPOOL_STOPS_BY_CLOSEST_TRANSIT_STOPS:
            carpool.stops = self._replace_stops_by_transit_stops(carpool, self.REPLACEMENT_STOPS_SERACH_RADIUS_IN_M)
 
        path = self._path_for_ride(carpool)
        lineString_shapely_wgs84 = LineString(coordinates = path["points"]["coordinates"]).simplify(0.0001)
        lineString_wgs84 = GeoJSONLineString(type="LineString", coordinates=list(lineString_shapely_wgs84.coords))
        virtual_stops = self.stops_store.find_additional_stops_around(lineString_wgs84, carpool.stops) 
        if not virtual_stops.empty:
            virtual_stops["time"] = self._estimate_times(path, virtual_stops['distance'])
            logger.debug("Virtual stops found: {}".format(virtual_stops))
        if len(virtual_stops) > MAX_STOPS_PER_TRIP:
            # in case we found more than MAX_STOPS_PER_TRIP, we retain first and last 
            # half of MAX_STOPS_PER_TRIP
            virtual_stops = virtual_stops.iloc[np.r_[0:int(MAX_STOPS_PER_TRIP/2), int(MAX_STOPS_PER_TRIP/2):]]
            
        trip_id = f"{carpool.agency}:{carpool.id}"
        stop_times = self._stops_and_stop_times(carpool.departureTime, trip_id, virtual_stops)
        
        enhanced_carpool = carpool.copy()
        enhanced_carpool.stops = stop_times
        enhanced_carpool.path = lineString_wgs84
        return enhanced_carpool

    def _convert_stop_times(self, carpool):

        stop_times = [GtfsStopTime(
                self._trip_id(carpool), 
                stop.arrivalTime, 
                stop.departureTime, 
                stop.id, 
                seq_nr+1,
                STOP_TIMES_STOP_TYPE_NONE if stop.pickup_dropoff == PickupDropoffType.only_dropoff else STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER, 
                STOP_TIMES_STOP_TYPE_NONE if stop.pickup_dropoff == PickupDropoffType.only_pickup else STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER, 
                STOP_TIMES_TIMEPOINT_APPROXIMATE) 
            for seq_nr, stop in enumerate(carpool.stops)]
        return stop_times

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
                if instructions[cnt]["distance"] ==0:
                    raise RoutingException("Origin and destinaction too close")
                percent_dist = (distance - cumulated_distance) / instructions[cnt]["distance"]
                stop_time = cumulated_time + percent_dist * instructions[cnt]["time"]
                stop_times.append(stop_time)
            else:
                logger.debug("distance {} exceeds total length {}, using max arrival time {}".format(distance, cumulated_distance, cumulated_time))
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

            if not current_stop.id:
                continue
            elif i == 0:
                if (stops_frame.iloc[1].time-current_stop.time) < 1000:
                    # skip custom stop if there is an official stop very close by
                    logger.debug("Skipped stop %s", current_stop.id)
                    continue
            else:
                if (current_stop.time-stops_frame.iloc[i-1].time) < 5000 and not i==1 and not is_carpooling_stop(current_stop.id, current_stop.stop_name):
                    # skip latter stop if it's very close (<5 seconds drive) by the preceding
                    logger.debug("Skipped stop %s", current_stop.id)
                    continue
            trip_time = timedelta(milliseconds=int(current_stop.time))
            is_dropoff = self._is_dropoff_stop(current_stop, total_distance)
            is_pickup = self._is_pickup_stop(current_stop, total_distance)
            # TODO would be nice if possible to publish a minimum shared distance 
            pickup_type = STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER if is_pickup else STOP_TIMES_STOP_TYPE_NONE
            dropoff_type = STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER if is_dropoff else STOP_TIMES_STOP_TYPE_NONE
            
            if is_pickup and not is_dropoff:
                pickup_dropoff = PickupDropoffType.only_pickup
            elif not is_pickup and is_dropoff:
                pickup_dropoff = PickupDropoffType.only_dropoff
            else:
                pickup_dropoff = PickupDropoffType.pickup_and_dropoff

            next_stop_time = first_stop_time + trip_time
            seq_nr += 1
            stop_times.append(StopTime(**{
                'arrivalTime': str(next_stop_time), 
                'departureTime': str(next_stop_time), 
                'id': current_stop.id, 
                'pickup_dropoff': pickup_dropoff,
                'name': str(current_stop.stop_name),
                'lat': current_stop.y,
                'lon': current_stop.x
                }))

        return stop_times
    
    def _is_dropoff_stop(self, current_stop, total_distance):
        return current_stop["distance"] >= 0.5 * total_distance
        
    def _is_pickup_stop(self, current_stop, total_distance):
        return current_stop["distance"] < 0.5 * total_distance

def load_carpool(agency_id: str, carpool_id: str, folder: str ='data/enhanced') -> Carpool:
    with open(f'{folder}/{agency_id}/{carpool_id}.json', 'r', encoding='utf-8') as f:
        dict = json.load(f)
        carpool = Carpool(**dict)
    return carpool

def carpool_exists(agency_id: str, carpool_id: str, folder: str ='data/enhanced'):
    return os.path.exists(f"{folder}/{agency_id}/{carpool_id}.json")

def remove_carpool_file(agency_id: str, carpool_id: str, folder: str ='data/enhanced'):
    return os.remove(f"{folder}/{agency_id}/{carpool_id}.json")
