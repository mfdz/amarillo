from collections import namedtuple
from datetime import timedelta, datetime

GtfsFeedInfo = namedtuple('GtfsFeedInfo', 'feed_id feed_publisher_name feed_publisher_url feed_lang feed_version')
GtfsAgency = namedtuple('GtfsAgency', 'agency_id agency_name agency_url agency_timezone agency_lang agency_email')
GtfsRoute = namedtuple('GtfsRoute',  'agency_id route_id route_long_name route_type route_url route_short_name route_desc')
GtfsStop = namedtuple('GtfsStop', 'stop_id stop_lat stop_lon stop_name')
GtfsStopTime = namedtuple('GtfsStopTime', 'trip_id departure_time arrival_time stop_id stop_sequence pickup_type drop_off_type timepoint')
GtfsTrip = namedtuple('GtfsTrip', 'route_id trip_id service_id shape_id trip_headsign bikes_allowed')
GtfsCalendar = namedtuple('GtfsCalendar', 'service_id start_date end_date monday tuesday wednesday thursday friday saturday sunday')
GtfsCalendarDate = namedtuple('GtfsCalendarDate', 'service_id date exception_type')
GtfsShape = namedtuple('GtfsShape','shape_id shape_pt_lon shape_pt_lat shape_pt_sequence')

EXCEPTION_TYPE_ADDED = 1
EXCEPTION_TYPE_REMOVED = 2

WEEKDAYS = ['Mo','Di','Mi','Do','Fr','Sa','So']

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


def _weekday_sequence(start, end):
    if end - start == 1:
        return f"{WEEKDAYS[start % 7]}, {WEEKDAYS[end % 7]}"
    elif end - start > 1:
        return f"{WEEKDAYS[start % 7]}-{WEEKDAYS[end % 7]}"
    return WEEKDAYS[start % 7]


def format_calendar(cal: GtfsCalendar, calendar_dates: GtfsCalendarDate | None) -> str:

    weekday_string = f"{cal.monday}{cal.tuesday}{cal.wednesday}{cal.thursday}{cal.friday}{cal.saturday}{cal.sunday}"

    start_weekday = -1
    sequences = []
    for weekday in range(14):
        active_period_started = start_weekday >= 0
        if active_period_started and weekday > start_weekday +6:
            if start_weekday >= 0 and end >= start_weekday:
                if len(sequences)>0:
                    sequences.pop(0)
                sequences.append([start_weekday, end])
            break
        if weekday > 6 and start_weekday < 0:
            break

        is_current_weekday_active = weekday_string[weekday % 7] == '1'
        if is_current_weekday_active:
            if not active_period_started:  
                start_weekday = weekday
            end = weekday
        elif active_period_started:
            if end > 6 and len(sequences)>0:
                sequences.pop(0)
            sequences.append([start_weekday, end])
            start_weekday = -1  # Reset for next block

    if len(sequences) > 0:
        weekdays_string = ", ".join([_weekday_sequence(s[0],s[1]) for s in sequences])
        if calendar_dates and len(calendar_dates) > 0:
            return f"{weekdays_string} (mit Ausnahmen)"
        return weekdays_string

    added_calendar_dates = [cd for cd in (calendar_dates or []) if cd.exception_type == EXCEPTION_TYPE_ADDED]
    if len(added_calendar_dates) > 0:
        parsed_date = datetime.strptime(added_calendar_dates[0].date, '%Y%m%d')
        datestring = datetime.strftime(parsed_date, '%d.%m.%Y')
        if len(added_calendar_dates) == 1:
            return datestring
        return f'{datestring} und weitere'
    return ""
