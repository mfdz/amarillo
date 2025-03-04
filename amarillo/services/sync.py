import asyncio
import logging
import time

import schedule

from amarillo.services.importing import (
    BessermitfahrenImporter,
    MyCarpoolAppImporter,
    NoiImporter,
    PendlerportalImporter,
    Ride2GoImporter,
)
from amarillo.services.secrets import secrets

logger = logging.getLogger(__name__)


class Syncer:
    def __init__(self, store, agency_service):
        self.store = store
        self.agency_service = agency_service

    def perform_full_sync(self):
        agencies = self.agency_service.get_all_agencies()
        for agency_id in agencies:
            try:
                asyncio.run(self.sync(agency_id))
            except Exception as e:
                logger.exception(f"Could not import {agency_id}: {e}")

    def schedule_full_sync(self, time_str):
        schedule.every().day.at(time_str).do(self.perform_full_sync)

    async def sync(self, agency_id):
        if agency_id == "ride2go":
            importer = Ride2GoImporter()
        elif agency_id == "ummadum":
            importer = NoiImporter(agency_id, test_mode=True)
        elif agency_id == "bessermitfahren":
            importer = BessermitfahrenImporter(secrets.bessermitfahren_url)
        elif agency_id == "pendlerportal":
            importer = PendlerportalImporter(secrets.pendlerportal_url)
        elif agency_id == "mycarpoolapp":
            importer = MyCarpoolAppImporter(secrets.mycarpoolapp_url)
        else:
            logger.warn(f"Agency {agency_id} does not exist")
            return None
            # raise ValueError(f"Agency {agency_id} does not exist.")

        carpools = importer.load_carpools()
        # Reduce current time by a minute to avoid inter process timestamp issues
        synced_files_older_than = time.time() - 60
        result = [await self.store.store_carpool(cp) for cp in carpools]
        await self.store.delete_agency_carpools_older_than(agency_id, synced_files_older_than)
        return result
