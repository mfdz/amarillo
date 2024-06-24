import json
from glob import glob
from typing import Dict

from amarillo.models.Carpool import Region


class RegionService:

    def __init__(self):
        self.regions: Dict[str, Region] = {}
        for region_file_name in glob('data/region/*.json'):
            with open(region_file_name) as region_file:
                dict = json.load(region_file)
                region = Region(**dict)
                region_id = region.id
                self.regions[region_id] = region

    def get_region(self, region_id: str) -> Region:
        region = self.regions.get(region_id)
        return region
