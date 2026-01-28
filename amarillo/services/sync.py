import asyncio
import logging
import time

import schedule

from amarillo.models.AgencyConf import AgencyConf, AgencyRole
from amarillo.services.importing import (
    AmarilloImporter,
    BessermitfahrenImporter,
    MobilityDIYImporter,
    MyCarpoolAppImporter,
    NoiImporter,
    PendlerportalImporter,
    Ride2GoImporter,
    SimplyHopImporter,
)

logger = logging.getLogger(__name__)


class Syncer:
    def __init__(self, store, agencyconf_service):
        self.store = store
        self.agencyconf_service = agencyconf_service

    def perform_full_sync(self) -> None:
        agencies_to_sync = [agency for agency in self.agencyconf_service.get_all_agencies() if self.should_sync(agency)]
        agency_ids_to_sync = [agency.agency_id for agency in agencies_to_sync]
        logger.info(f"Perform full sync for agencies {agency_ids_to_sync}")
        for agency in agencies_to_sync:
            try:
                asyncio.run(self.sync(agency.agency_id, agency.offers_download_url, agency.offers_download_http_headers))
            except Exception as e:
                logger.exception(f"Could not import {agency.agency_id}: {e}")

    def should_sync(self, agency: AgencyConf) -> bool:
        return agency.offers_download_url is not None and AgencyRole.carpool_agency in agency.roles

    def schedule_full_sync(self, time_str):
        schedule.every().day.at(time_str).do(self.perform_full_sync)

    async def sync(self, agency_id: str, offers_download_url=None, offers_download_http_headers=None):
        if agency_id == "ride2go":
            importer = Ride2GoImporter(offers_download_url, offers_download_http_headers)
        elif agency_id == "ummadum":
            importer = NoiImporter(agency_id, test_mode=True)
        elif agency_id == "bessermitfahren":
            importer = BessermitfahrenImporter(offers_download_url)
        elif agency_id == "pendlerportal":
            importer = PendlerportalImporter(offers_download_url)
        elif agency_id == "mycarpoolapp":
            importer = MyCarpoolAppImporter(offers_download_url)
        elif agency_id == 'matchrider':
            importer = MobilityDIYImporter(offers_download_url, offers_download_http_headers)
        elif agency_id == 'simplyhop':
            importer = SimplyHopImporter(agency_id, offers_download_url, offers_download_http_headers)
        else:
            importer = AmarilloImporter(agency_id, offers_download_url, offers_download_http_headers)

        sync_start_time = time.time()
        logger.info(f"Start sync for agency {agency_id} at {sync_start_time}")

        carpools = importer.load_carpools()

        result = [await self.store.store_carpool(cp) for cp in carpools]
        logger.info(f"Synced {len(result)} offers for agency {agency_id}")
        
        await self.store.delete_agency_carpools_older_than(agency_id, sync_start_time)
        return result
