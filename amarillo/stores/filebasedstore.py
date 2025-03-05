import json
import logging 
import os
import re
from datetime import datetime
from glob import glob
from pathlib import Path

from amarillo.models.Carpool import Carpool

logger = logging.getLogger(__name__)

class FileBasedStore:

    async def set_lastUpdated_if_unset(self, carpool):
        if carpool.lastUpdated is None:
            carpool.lastUpdated = datetime.now()

    async def does_agency_exist(self, agency_id: str):
        return os.path.exists(f"conf/agency/{agency_id}.json")

    async def does_carpool_exist(self, agency_id: str, carpool_id: str):
        return os.path.exists(f"data/carpool/{agency_id}/{carpool_id}.json")

    async def store_carpool(self, carpool: Carpool) -> Carpool:
        await self.set_lastUpdated_if_unset(carpool)
        await self.save_carpool(carpool)

        return carpool

    async def save_carpool(self, carpool, folder: str = "data/carpool"):
        with open(f"{folder}/{carpool.agency}/{carpool.id}.json", "w", encoding="utf-8") as f:
            f.write(carpool.model_dump_json())

    async def load_carpool(self, agency_id, carpool_id) -> Carpool:
        with open(f"data/carpool/{agency_id}/{carpool_id}.json", "r", encoding="utf-8") as f:
            dict = json.load(f)
            carpool = Carpool(**dict)
        return carpool

    async def delete_agency_carpools_older_than(self, agency_id, timestamp):
        for carpool_file_name in glob(f"data/carpool/{agency_id}/*.json"):
            if os.path.getmtime(carpool_file_name) < timestamp:
                m = re.search(r"([a-zA-Z0-9_-]+)\.json$", carpool_file_name)
                # TODO log deletion
                await self.delete_carpool(agency_id, m[1])

    async def delete_carpool(self, agency_id: str, carpool_id: str):
        logger.info(f"Delete carpool {agency_id}:{carpool_id}.")
        cp = await self.load_carpool(agency_id, carpool_id)
        logger.info(f"Loaded carpool {agency_id}:{carpool_id}.")
        # load and store, to receive pyinotify events and have file timestamp updated
        await self.save_carpool(cp, "data/trash")
        logger.info(f"Saved carpool {agency_id}:{carpool_id} in trash.")
        if Path(f"data/carpool/{agency_id}/{carpool_id}.json").is_file():
            os.remove(f"data/carpool/{agency_id}/{carpool_id}.json")
            if Path(f"data/carpool/{agency_id}/{carpool_id}.json").is_file():
                logger.error(f"Deletion of 'data/carpool/{agency_id}/{carpool_id}.json' failed")
            else:
                logger.info(f"Deleted 'data/carpool/{agency_id}/{carpool_id}.json'")
