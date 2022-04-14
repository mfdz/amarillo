from app.models.Carpool import Region
from app.services.gtfs_export import GtfsExport, GtfsFeedInfo, GtfsAgency
from app.services.gtfs import GtfsRtProducer
from app.utils.container import container
import schedule
import threading
import time
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

regions = [
	Region(**{'id': 'bb', 'bbox': [11.26, 51.36, 14.77, 53.56]}),
	Region(**{'id': 'bw', 'bbox': [49.79,  7.51, 47.54, 10.5]}),
	Region(**{'id': 'by', 'bbox': [50.56,  8.97, 47.28, 13.86]}),
	Region(**{'id': 'nrw', 'bbox': [52.53,  5.86, 50.33, 9.45]})
]
# TODO access agencies defined via model
agencies = [ 
	GtfsAgency('ride2go', 'ride2go', 'http://www.ride2go.de', 'Europe/Berlin', 'de', 'info@ride2go.com'),
	GtfsAgency('fg', 'Fahrgemeinschaft.de', 'http://www.fahrgemeinschaft.de', 'Europe/Berlin', 'de', 'hilfe@adac-mitfahrclub.de'),
	GtfsAgency('mifaz', 'mifaz.de', 'http://www.mifaz.de', 'Europe/Berlin', 'de', 'info@mifaz.de'),
]
def run_schedule():
	while 1:
		try:
			schedule.run_pending()
		except Exception as e:
			logger.exception(e)
		time.sleep(1)

def midnight():
	yesterday = date.today()-timedelta(days=1)
	container['trips_store'].purge_trips_older_than(yesterday)
	generate_gtfs()

def generate_gtfs():
	logger.info("Generate GTFS")

	for region in regions:
		feed_info = GtfsFeedInfo('mfdz', 'MITFAHR|DE|ZENTRALE', 'http://www.mitfahrdezentrale.de', 'de', 1)
		exporter = GtfsExport(
			agencies, 
			feed_info, 
			container['trips_store'], 
			container['stops_store'], 
			region.bbox)
		exporter.export(f"gtfs/mfdz.{region.id}.gtfs.zip", "target/")

def generate_gtfs_rt():
	logger.info("Generate GTFS-RT")
	# TODO generate temp file and re-link to afterwards
	for region in regions:
		rt = GtfsRtProducer().generate_feed(time.time(), format='protobuff', bbox=region.bbox)
		with open(f"gtfs/mfdz.{region.id}.gtfsrt.pbf", "wb") as f:
			f.write(rt)

def start_schedule():
	schedule.every().day.at("00:00").do(midnight)
	#schedule.every(10).seconds.do(midnight)
	schedule.every(60).seconds.do(generate_gtfs_rt)
	job_thread = threading.Thread(target=run_schedule, daemon=True)
	job_thread.start()