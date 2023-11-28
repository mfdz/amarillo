
from collections.abc import Iterable
from datetime import datetime, timedelta
from zipfile import ZipFile
import csv
import gettext
import logging
import re

from app.utils.utils import assert_folder_exists
from app.models.gtfs import GtfsTimeDelta, GtfsFeedInfo, GtfsAgency, GtfsRoute, GtfsStop, GtfsStopTime, GtfsTrip, GtfsCalendar, GtfsCalendarDate, GtfsShape
from app.services.stops import is_carpooling_stop
from app.services.gtfs_constants import *


logger = logging.getLogger(__name__)

class GtfsExport:
    
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
        assert_folder_exists(gtfsfolder)
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
            if self.bbox is None or trip.intersects(self.bbox):
                self._convert_trip(trip)
    
    def _convert_trip(self, trip):
        self.routes_counter += 1
        self.routes.append(self._create_route(trip))
        self.calendar.append(self._create_calendar(trip))
        if not trip.runs_regularly:
            self.calendar_dates.append(self._create_calendar_date(trip))
        self.trips.append(self._create_trip(trip, self.routes_counter))
        self._append_stops_and_stop_times(trip)
        self._append_shapes(trip, self.routes_counter)
    
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
   
    def _create_route(self, trip): 
        return GtfsRoute(trip.agency, trip.trip_id, trip.route_long_name(), RIDESHARING_ROUTE_TYPE, trip.url, "")
        
    def _create_calendar(self, trip):
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
        return GtfsCalendar(trip.trip_id, stop_date, self._convert_stop_date(feed_start_date + timedelta(days=31)), *(trip.weekdays))
    
    def _create_calendar_date(self, trip):
        return GtfsCalendarDate(trip.trip_id, self._convert_stop_date(trip.start), CALENDAR_DATES_EXCEPTION_TYPE_ADDED)
    
    def _create_trip(self, trip, shape_id):
        return GtfsTrip(trip.trip_id, trip.trip_id, trip.trip_id, shape_id, trip.trip_headsign, NO_BIKES_ALLOWED)
    
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
        
    def _append_stops_and_stop_times(self, trip):
        # Assumptions: 
        # arrival_time = departure_time
        # pickup_type, drop_off_type for origin: = coordinate/none
        # pickup_type, drop_off_type for destination: = none/coordinate
        # timepoint = approximate for origin and destination (not sure what consequences this might have for trip planners)
        for stop_time in trip.stop_times:
            # retrieve stop from stored_stops and mark it to be exported
            wkn_stop = self.stored_stops.get(stop_time.stop_id)
            if not wkn_stop:
                logger.warning("No stop found in stop_store for %s. Will skip stop_time %s of trip %s", stop_time.stop_id, stop_time.stop_sequence, trip.trip_id)
            else:
                self.stops[stop_time.stop_id] = wkn_stop
                # Append stop_time
                self.stop_times.append(stop_time)
        
    def _append_shapes(self, trip, shape_id):
        counter = 0
        for point in trip.path.coordinates:
                counter += 1
                self.shapes.append(GtfsShape(shape_id, point[0], point[1], counter))
            
    def _stop_hash(self, stop):
        return "{}#{}#{}".format(stop.stop_name,stop.x,stop.y)
        
    def _should_always_export(self, stop):
        """ 
        Returns true, if the given stop shall be exported to GTFS,
        regardless, if it's part of a trip or not.

        This is necessary, as potential stops are required 
        to be part of the GTFS to be referenced later on 
        by dynamicly added trips.
        """
        if self.bbox:
            return (self.bbox[0] <= stop.stop_lon <= self.bbox[2] and 
                self.bbox[1] <= stop.stop_lat <= self.bbox[3])
        else:
            return is_carpooling_stop(stop.stop_id, stop.stop_name)
            
    def _load_stored_stop(self, stop):
        gtfsstop = self._convert_stop(stop)
        stop_hash = self._stop_hash(stop)
        self.stored_stops[gtfsstop.stop_id] = gtfsstop
        if self._should_always_export(gtfsstop):
            self.stops[gtfsstop.stop_id] = gtfsstop

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

    