from collections import namedtuple
from datetime import timedelta

GtfsFeedInfo = namedtuple('GtfsFeedInfo', 'feed_id feed_publisher_name feed_publisher_url feed_lang feed_version')
GtfsAgency = namedtuple('GtfsAgency', 'agency_id agency_name agency_url agency_timezone agency_lang agency_email')
GtfsRoute = namedtuple('GtfsRoute',  'agency_id route_id route_long_name route_type route_url route_short_name')
GtfsStop = namedtuple('GtfsStop', 'stop_id stop_lat stop_lon stop_name')
GtfsStopTime = namedtuple('GtfsStopTime', 'trip_id departure_time arrival_time stop_id stop_sequence pickup_type drop_off_type timepoint')
GtfsTrip = namedtuple('GtfsTrip', 'route_id trip_id service_id shape_id trip_headsign bikes_allowed')
GtfsCalendar = namedtuple('GtfsCalendar', 'service_id start_date end_date monday tuesday wednesday thursday friday saturday sunday')
GtfsCalendarDate = namedtuple('GtfsCalendarDate', 'service_id date exception_type')
GtfsShape = namedtuple('GtfsShape','shape_id shape_pt_lon shape_pt_lat shape_pt_sequence')

# TODO Move to utils
class GtfsTimeDelta(timedelta):
    def __str__(self):
        seconds = self.total_seconds()
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        str = '{:02d}:{:02d}:{:02d}'.format(int(hours), int(minutes), int(seconds))
        return (str)
        
    def __add__(self, other):
        if isinstance(other, timedelta):
            return self.__class__(self.days + other.days,
                                  self.seconds + other.seconds,
                                  self.microseconds + other.microseconds)
        return NotImplemented