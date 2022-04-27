from app.models.Carpool import Region
from app.services.gtfs_export import GtfsExport, GtfsFeedInfo, GtfsAgency
from app.services.gtfs import GtfsRtProducer
from app.utils.container import container
from glob import glob
import json
import schedule
import threading
import time
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

regions = {}
for region_file_name in glob('conf/region/*.json'):
    with open(region_file_name) as region_file:
        dict = json.load(region_file)
        region = Region(**dict)
        region_id = region.id
        regions[region_id] = region

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

	for region in regions.values():
		# TODO make feed producer infos configurable
		feed_info = GtfsFeedInfo('mfdz', 'MITFAHR|DE|ZENTRALE', 'http://www.mitfahrdezentrale.de', 'de', 1)
		exporter = GtfsExport(
			agencies, 
			feed_info, 
			container['trips_store'], 
			container['stops_store'], 
			region.bbox)
		exporter.export(f"data/gtfs/amarillo.{region.id}.gtfs.zip", "data/tmp/")

def generate_gtfs_rt():
	logger.info("Generate GTFS-RT")
	producer = GtfsRtProducer(container['trips_store'])
	for region in regions.values():
		rt = producer.export_feed(time.time(), f"data/gtfs/amarillo.{region.id}.gtfsrt", bbox=region.bbox)

def start_schedule():
	schedule.every().day.at("00:00").do(midnight)
	schedule.every(60).seconds.do(generate_gtfs_rt)
	# Create all feeds once at startup
	schedule.run_all()
	job_thread = threading.Thread(target=run_schedule, daemon=True)
	job_thread.start()