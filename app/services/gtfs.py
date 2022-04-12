import app.services.gtfsrt.gtfs_realtime_pb2 as gtfs_realtime_pb2
import app.services.gtfsrt.realtime_extension_pb2 as mfdzrte
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import ParseDict
import time
# TODO only temporarilly 
import app.services.mocks as mocks

def gtfs_rt(carpools, format='protobuf'):
	# See https://developers.google.com/transit/gtfs-realtime/reference
	# https://github.com/mfdz/carpool-gtfs-rt/blob/master/src/main/java/de/mfdz/resource/CarpoolResource.java
	gtfsrt_dict = {
		'header': {
			'gtfsRealtimeVersion': '1.0', 
			'timestamp': int(time.time())
		}, 
		'entity': [mocks.mock_trip_updated_added, mocks.mock_trip_updated_deleted]
	}
	feed = gtfs_realtime_pb2.FeedMessage()
	ParseDict(gtfsrt_dict, feed)

	if "json" == format.lower():
		return MessageToDict(feed)
	else:
		return feed.SerializeToString()