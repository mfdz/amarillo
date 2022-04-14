
from collections.abc import Iterable
from datetime import datetime, timedelta
from zipfile import ZipFile
import csv
import gettext
import logging
import re
import os
from app.models.gtfs import GtfsTimeDelta, GtfsFeedInfo, GtfsAgency, GtfsRoute, GtfsStop, GtfsStopTime, GtfsTrip, GtfsCalendar, GtfsCalendarDate, GtfsShape

logger = logging.getLogger(__name__)

class GtfsExport:
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
    
    stops_counter = 0
    trips_counter = 0
    routes_counter = 0

    stored_stops = {}
    
    def __init__(self, agencies, feed_info, ridestore, stopstore, bbox = None):
        self.stops = {}
        self.routes = []
        self.calendar_dates = []
        self.calendar = []
        self.trips = []
        self.stop_times = []
        self.calendar = []
        self.shapes = []
        self.agencies = agencies
        self.feed_info = feed_info
        self.localized_to = " nach "
        self.localized_short_name = "Mitfahrgelegenheit"
        self.stopstore = stopstore
        self.ridestore = ridestore
        self.bbox = bbox
            
    def export(self, gtfszip_filename, gtfsfolder):
        self._assert_folder_exists(gtfsfolder)
        self._prepare_gtfs_feed(self.ridestore, self.stopstore)
        self._write_csvfile(gtfsfolder, 'agency.txt', self.agencies)
        self._write_csvfile(gtfsfolder, 'feed_info.txt', self.feed_info)
        self._write_csvfile(gtfsfolder, 'routes.txt', self.routes)
        self._write_csvfile(gtfsfolder, 'trips.txt', self.trips)
        self._write_csvfile(gtfsfolder, 'calendar.txt', self.calendar)
        self._write_csvfile(gtfsfolder, 'calendar_dates.txt', self.calendar_dates)
        self._write_csvfile(gtfsfolder, 'stops.txt', self.stops.values())
        self._write_csvfile(gtfsfolder, 'stop_times.txt', self.stop_times)
        self._write_csvfile(gtfsfolder, 'shapes.txt', self.shapes)
        self._zip_files(gtfszip_filename, gtfsfolder)
    
    def _assert_folder_exists(self, foldername):
        if not os.path.isdir(foldername):
            os.makedirs(foldername)

    def _zip_files(self, gtfszip_filename, gtfsfolder):
        gtfsfiles = ['agency.txt', 'feed_info.txt', 'routes.txt', 'trips.txt', 
                'calendar.txt', 'calendar_dates.txt', 'stops.txt', 'stop_times.txt', 'shapes.txt']
        with ZipFile(gtfszip_filename, 'w') as gtfszip:
            for gtfsfile in gtfsfiles:
                gtfszip.write(gtfsfolder+'/'+gtfsfile, gtfsfile)
        
    def _prepare_gtfs_feed(self, ridestore, stopstore):
        """
        Prepares all gtfs objects in memory before they are written
        to their respective streams.
        
        For all wellknown stops a GTFS stop is created and
        afterwards all ride offers are transformed into their
        gtfs equivalents.
        """
        for stopSet in stopstore.stopsDataFrames:
            for stop in stopSet["stops"].itertuples():
                self._load_stored_stop(stop)
        cloned_trips = dict(ridestore.trips)
        for url, trip in cloned_trips.items():
            self._convert_trip(trip)
    
    def _convert_trip(self, trip):
        self.routes_counter += 1
        self.routes.append(self._create_route(self.routes_counter, trip))
        self.calendar.append(self._create_calendar(self.routes_counter, trip))
        if not trip.runs_regularly:
            self.calendar_dates.append(self._create_calendar_date(self.routes_counter, trip))
        self.trips.append(self._create_trip(self.routes_counter, self._trip_headsign(trip.stops.tail(1).iloc(0)[0]["stop_name"])))
        self._append_stops_and_stop_times(self.routes_counter, trip)
        self._append_shapes(self.routes_counter, trip)
    
    def _trip_headsign(self, destination):
        destination = destination.replace('(Deutschland)', '')
        destination = destination.replace(', Deutschland', '')
        appendix = ''
        if 'Schweiz' in destination or 'Switzerland' in destination:
            appendix = ', Schweiz'
            destination = destination.replace('(Schweiz)', '')
            destination = destination.replace(', Schweiz', '')
            destination = destination.replace('(Switzerland)', '')
        
        try:
            matches = re.match(r"(.*,)? ?(\d{4,5})? ?(.*)", destination)
        
            match = matches.group(3).strip() if matches != None else destination.strip()
            if match[-1]==')' and not '(' in match:
                match = match[0:-1] 
        
            return match + appendix
        except Exception as ex:
            logger.error("error for "+destination )
            logger.exception(ex)
            return destination
   
    def _create_route(self, route_id, trip): 
        return GtfsRoute(trip.agency, route_id, trip.route_long_name(), self.RIDESHARING_ROUTE_TYPE, trip.url, "")
        
    def _create_calendar(self, service_id, trip):
        # TODO currently, calendar is not provided by Fahrgemeinschaft.de interface.
        # We could apply some heuristics like requesting multiple days and extrapolate
        # if multiple trips are found, but better would be to have these provided by the
        # offical interface. Then validity periods should be provided as well (not
        # sure if these are available)
        # For fahrgemeinschaft.de, regurlar trips are recognizable via their url
        # which contains "regelmaessig". However, we don't know on which days of the week,
        # nor until when. As a first guess, if datetime is a mo-fr, we assume each workday,
        # if it's sa/su, only this...
        
        feed_start_date = datetime.today()
        stop_date = self._convert_stop_date(feed_start_date)
        return GtfsCalendar(service_id, stop_date, self._convert_stop_date(feed_start_date + timedelta(days=31)), *(trip.weekdays))
    
    def _create_calendar_date(self, service_id, trip):
        return GtfsCalendarDate(service_id, self._convert_stop_date(trip.start), self.CALENDAR_DATES_EXCEPTION_TYPE_ADDED)
    
    def _create_trip(self, route_trip_service_id, trip_headsign):
        return GtfsTrip(route_trip_service_id, route_trip_service_id, route_trip_service_id, route_trip_service_id, trip_headsign, self.NO_BIKES_ALLOWED)
    
    def _convert_stop(self, stop):
        """
        Converts a stop represented as pandas row to a gtfs stop.
        Expected attributes of stop: id, stop_name, x, y (in wgs84)
        """
        if stop.id:
            id = stop.id
        else:
            self.stops_counter += 1
            id = "tmp-{}".format(self.stops_counter)

        stop_name = "k.A." if stop.stop_name is None else stop.stop_name
        return GtfsStop(id, stop.y, stop.x, stop_name)
        
    def _append_stops_and_stop_times(self, trip_id, trip):
        # Assumptions: 
        # arrival_time = departure_time
        # pickup_type, drop_off_type for origin: = coordinate/none
        # pickup_type, drop_off_type for destination: = none/coordinate
        # timepoint = approximate for origin and destination (not sure what consequences this might have for trip planners)
        number_of_stops = len(trip.stops.index)
        total_distance = trip.stops.iloc[number_of_stops-1]["distance"]
        
        first_stop_time = GtfsTimeDelta(hours = trip.start_time.hour, minutes = trip.start_time.minute, seconds = trip.start_time.second) 
            
        for i in range(0, number_of_stops):
            current_stop = trip.stops.iloc[i]
            if i == 0:
                if (trip.stops.iloc[1].time-current_stop.time) < 1000:
                    # skip custom stop if there is an official stop very close by
                    logger.debug("Skipped stop {}", current_stop)
                    continue
            else:
                if (current_stop.time-trip.stops.iloc[i-1].time) < 5000:
                    # skip latter stop if it's very close (<5 seconds drive) by the preceding
                    logger.debug("Skipped stop {}", current_stop)
                    continue
            
            trip_time = timedelta(milliseconds=int(current_stop.time))
            is_dropoff = self._is_dropoff_stop(current_stop, total_distance)
            is_pickup = self._is_pickup_stop(current_stop, total_distance)
            # TODO would be nice if possible to publish a minimum shared distance 
            pickup_type = self.STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER if is_pickup else self.STOP_TIMES_STOP_TYPE_NONE
            dropoff_type = self.STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER if is_dropoff else self.STOP_TIMES_STOP_TYPE_NONE
            
            stop = self._get_or_create_stop(current_stop)
            next_stop_time = first_stop_time + trip_time
            self.stop_times.append(GtfsStopTime(trip_id, str(next_stop_time), str(next_stop_time), stop.stop_id, i+1, pickup_type, dropoff_type, self.STOP_TIMES_TIMEPOINT_APPROXIMATE))
   
    def _is_dropoff_stop(self, current_stop, total_distance):
        return current_stop["distance"] >= 0.5 * total_distance
        
    def _is_pickup_stop(self, current_stop, total_distance):
        return current_stop["distance"] < 0.5 * total_distance
        
    def _append_shapes(self, route_id, trip):
        counter = 0
        for point in trip.path['points']['coordinates']:
                counter += 1
                self.shapes.append(GtfsShape(route_id, point[0], point[1], counter))
            
    def _stop_hash(self, stop):
        return "{}#{}#{}".format(stop.stop_name,stop.x,stop.y)
        
    def _should_always_export(self, stop):
        ### stops with a stop_id equal to mfdz: or a name containing the string mitfahr
        ### should be retained as carpool stops, even if no trip passes by
        stop_name = stop.stop_name.lower() 
        #return stop.stop_id.startswith('de:11') or stop.stop_id.startswith('de:12') or stop.stop_id.startswith('mfdz:') or 'mitfahr' in stop_name or 'p&m' in stop_name 
        return stop.stop_id.startswith('de:05') or stop.stop_id.startswith('mfdz:') or 'mitfahr' in stop_name or 'p&m' in stop_name 

    def _load_stored_stop(self, stop):
        gtfsstop = self._convert_stop(stop)
        stop_hash = self._stop_hash(stop)
        self.stored_stops[stop_hash] = gtfsstop
        if self._should_always_export(gtfsstop):
            self.stops[stop_hash] = gtfsstop

    def _get_stop_by_hash(self, stop_hash):
        return self.stops.get(stop_hash, self.stored_stops.get(stop_hash))
    
    def _get_or_create_stop(self, stop):
        stop_hash = self._stop_hash(stop)
        gtfsstop = self.stops.get(stop_hash)
        if gtfsstop is None:
            gtfsstop = self.stored_stops.get(stop_hash, self._convert_stop(stop))
            self.stops[stop_hash] = gtfsstop
        return gtfsstop
            
    def _convert_stop_date(self, date_time):
        return date_time.strftime("%Y%m%d")
        
    def _convert_stop_time(self, date_time):
        return date_time.strftime("%H:%M:%S")
    
    def _write_csvfile(self, gtfsfolder, filename, content):
        with open(gtfsfolder+"/"+filename, 'w', newline="\n", encoding="utf-8") as csvfile:
            self._write_csv(csvfile, content)
    
    def _write_csv(self, csvfile, content):
        if hasattr(content, '_fields'):
            writer = csv.DictWriter(csvfile, content._fields)
            writer.writeheader()
            writer.writerow(content._asdict())
        else:
            if content:
                writer = csv.DictWriter(csvfile, next(iter(content))._fields)
                writer.writeheader()
                for record in content:
                    writer.writerow(record._asdict())

    