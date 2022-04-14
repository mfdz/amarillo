from app.services.gtfs_export import GtfsExport, GtfsFeedInfo, GtfsAgency
import schedule
import threading
import time

def run_schedule():
	while 1:
		schedule.run_pending()c
		time.sleep(1)

def generate_gtfs():
	print("Generate GTFS")
	# TODO access agencies defined via model
	agencies = [ 
		GtfsAgency('fg', 'Fahrgemeinschaft.de', 'http://www.fahrgemeinschaft.de', 'Europe/Berlin', 'de', 'hilfe@adac-mitfahrclub.de'),
		GtfsAgency('mifaz', 'mifaz.de', 'http://www.mifaz.de', 'Europe/Berlin', 'de', 'info@mifaz.de'),
	]
	feed_info = GtfsFeedInfo('mfdz', 'MITFAHR|DE|ZENTRALE', 'http://www.mitfahrdezentrale.de', 'de', 1)
	exporter = GtfsExport(agencies, feed_info, trip_store, stop_store)
	# TODO generate region specific feed
	exporter.export("gtfs/mfdz.gtfs.zip", "target/")

def generate_gtfs_rt():
	print("Generate GTFS-RT")
	rt = GtfsRtProducer().generate_feed(time.time())
	# TODO write out pbf
	# TODO re-link to minimize

def start_schedule():
	schedule.every().day.at("10:30").do(generate_gtfs)
	# schedule.every(30).seconds.do(generate_gtfs_rt)
	job_thread = threading.Thread(target=run_schedule, daemon=True)
	job_thread.start()