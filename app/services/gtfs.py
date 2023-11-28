import app.services.gtfsrt.gtfs_realtime_pb2 as gtfs_realtime_pb2
import app.services.gtfsrt.realtime_extension_pb2 as mfdzrte
from app.services.gtfs_constants import *
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import ParseDict
from datetime import datetime, timedelta
import json
import re
import time

class GtfsRtProducer():

	def __init__(self, trip_store):
		self.trip_store = trip_store

	def generate_feed(self, time, format='protobuf', bbox=None):
		# See https://developers.google.com/transit/gtfs-realtime/reference
		# https://github.com/mfdz/carpool-gtfs-rt/blob/master/src/main/java/de/mfdz/resource/CarpoolResource.java
		gtfsrt_dict = {
			'header': {
				'gtfsRealtimeVersion': '1.0', 
				'timestamp': int(time)
			}, 
			'entity': self._get_trip_updates(bbox)
		}
		feed = gtfs_realtime_pb2.FeedMessage()
		ParseDict(gtfsrt_dict, feed)

		if "message" == format.lower():
			return feed
		elif "json" == format.lower():
			return MessageToDict(feed)
		else:
			return feed.SerializeToString()

	def export_feed(self, timestamp, file_path, bbox=None):
		"""
		Exports gtfs-rt feed as .json and .pbf file to file_path
		""" 
		feed = self.generate_feed(timestamp, "message", bbox)
		with open(f"{file_path}.pbf", "wb") as f:
			f.write(feed.SerializeToString())
		with open(f"{file_path}.json", "w") as f:
			json.dump(MessageToDict(feed), f)

	def _get_trip_updates(self, bbox = None):
		trips = []
		trips.extend(self._get_added(bbox))
		trips.extend(self._get_deleted(bbox))
		trip_updates = []
		for num, trip in enumerate(trips):
   			trip_updates.append( {
   				'id': f'carpool-update-{num}', 
  				'tripUpdate': trip
  				}
  			)
		return trip_updates

	def _get_deleted(self, bbox = None):
		return self._get_updates(
			self.trip_store.recently_deleted_trips(),
			self._as_delete_updates,
			bbox)

	def _get_added(self, bbox = None):
		return self._get_updates(
			self.trip_store.recently_added_trips(),
			self._as_added_updates,
			bbox)
	
	def _get_updates(self, trips, update_func, bbox = None):
		updates = []
		today = datetime.today()
		for t in trips:
			if bbox == None or t.intersects(bbox):
				updates.extend(update_func(t, today))
		return updates

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
		startdate = datetime.strptime(fromdate, '%Y%m%d')
		m = re.search(r'(\d+):(\d+):(\d+)', stop_time)
		delta = timedelta(
			hours=int(m.group(1)),
			minutes=int(m.group(2)),
			seconds=int(m.group(3)))
		return time.mktime((startdate + delta).timetuple())
	
	def _to_stop_times(self, trip, fromdate):
		return [{
		      'stopSequence': stoptime.stop_sequence, 
		      'arrival': {
		        'time': self._to_seconds(fromdate, stoptime.arrival_time),
		        'uncertainty': MFDZ_DEFAULT_UNCERTAINITY
		      },
		      'departure': {
		        'time':  self._to_seconds(fromdate, stoptime.departure_time),
		        'uncertainty': MFDZ_DEFAULT_UNCERTAINITY
		      }, 
		      'stopId': stoptime.stop_id, 
		      'scheduleRelationship': 'SCHEDULED',
		      'stop_time_properties': {
		        '[transit_realtime.stop_time_properties]': {
		          'dropoffType': 'COORDINATE_WITH_DRIVER' if stoptime.drop_off_type == STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER else 'NONE',
		          'pickupType': 'COORDINATE_WITH_DRIVER' if stoptime.pickup_type == STOP_TIMES_STOP_TYPE_COORDINATE_DRIVER else 'NONE'
		        }
		      }
		    }
			for stoptime in trip.stop_times]

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
				    'route_long_name' : trip.route_long_name(),
				    'route_type': RIDESHARING_ROUTE_TYPE
			    	}
		    },
		    'stopTimeUpdate': self._to_stop_times(trip, trip_date)
		} for trip_date in trip.next_trip_dates(fromdate)]
