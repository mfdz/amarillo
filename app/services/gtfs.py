import app.services.gtfsrt.gtfs_realtime_pb2 as gtfs_realtime_pb2
import app.services.gtfsrt.realtime_extension_pb2 as mfdzrte
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import ParseDict
import time
from datetime import datetime
# TODO only temporarilly 
import app.services.mocks as mocks
from app.utils.container import container

class GtfsRtProducer():

	def __init__(self):
		pass

	def generate_feed(self, time, format='protobuf'):
		# See https://developers.google.com/transit/gtfs-realtime/reference
		# https://github.com/mfdz/carpool-gtfs-rt/blob/master/src/main/java/de/mfdz/resource/CarpoolResource.java
		gtfsrt_dict = {
			'header': {
				'gtfsRealtimeVersion': '1.0', 
				'timestamp': int(time)
			}, 
			'entity': self._get_trip_updates()
		}
		feed = gtfs_realtime_pb2.FeedMessage()
		ParseDict(gtfsrt_dict, feed)

		if "json" == format.lower():
			return MessageToDict(feed)
		else:
			return feed.SerializeToString()

	def _get_trip_updates(self):
		trips = []
		trips.extend(self._get_added())
		trips.extend(self._get_deleted())		
		print(trips)
		trip_updates = []
		for num, trip in enumerate(trips):
   			trip_updates.append( {
   				'id': f'carpool-update-{num}', 
  				'tripUpdate': trip
  				}
  			)
		return trip_updates

	def _get_deleted(self):
		deleted = []
		for t in container['trips_store'].deleted_trips.values():
			deleted.extend(self._as_delete_updates(t, datetime.today()))
		return deleted

	def _get_added(self):
		recent = []
		for t in container['trips_store'].recent_trips.values():
			recent.extend(self._as_added_updates(t, datetime.today()))
		return recent

	def _as_delete_updates(self, trip, fromdate):
		return [{ 
		    'trip': {
		      'tripId': trip.trip_id, 
		      'startTime': trip.start_time_str(),
		      'startDate': trip_date, 
		      'scheduleRelationship': 'CANCELED', 
		      'routeId': trip.trip_id
		    }
		} for trip_date in trip.next_trip_dates(fromdate)]

	def _to_seconds(self, fromdate, stop_time):
		tt = datetime.strptime(f'{fromdate}-{stop_time}', '%Y%m%d-%H:%M:%S').timetuple()
		return time.mktime(tt)
	
	def _to_stop_times(self, trip, fromdate):
		return [{
		      'stopSequence': idx, 
		      'arrival': {
		        'time': self._to_seconds(fromdate, stoptime.arrival_time),
		        'uncertainty': 600
		      },
		      'departure': {
		        'time':  self._to_seconds(fromdate, stoptime.departure_time),
		        'uncertainty': 600
		      }, 
		      'stopId': stoptime.stop_id, 
		      'scheduleRelationship': 'SCHEDULED',
		      'stop_time_properties': {
		        '[transit_realtime.stop_time_properties]': {
		          'dropoffType': 'COORDINATE_WITH_DRIVER' if stoptime.drop_off_type == 3 else 'NONE',
		          'pickupType': 'COORDINATE_WITH_DRIVER' if stoptime.pickup_type == 3 else 'NONE'
		        }
		      }
		    }
			for idx, stoptime in trip.stops_and_stop_times()]

	def _as_added_updates(self, trip, fromdate):
		return [{ 
		    'trip': {
		      'tripId': trip.trip_id, 
		      'startTime': trip.start_time_str(),
		      'startDate': trip_date, 
		      'scheduleRelationship': 'ADDED', 
		      'routeId': trip.trip_id,
		      '[transit_realtime.trip_descriptor]': { 
					'routeUrl' : trip.url,
				    'agencyId' : trip.agency,
				    'route_long_name' : trip.route_long_name()
			    	}
		    },
		    'stopTimeUpdate': self._to_stop_times(trip, trip_date)
		} for trip_date in trip.next_trip_dates(fromdate)]

def gtfs_rt(carpools, format='protobuf'):
	return GtfsRtProducer().generate_feed(time.time(), format)
