import logging
import time
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from amarillo.models.Carpool import Region
from amarillo.routers.agencyconf import verify_admin_api_key
from amarillo.services.regions import RegionService
from amarillo.utils.container import container
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/region",
    tags=["region"]
)

@router.get("/",
            operation_id="getRegions",
            summary="Return all regions",
            response_model=List[Region],
            responses={
            },
            )
async def get_regions() -> List[Region]:
    service: RegionService = container['regions']
    
    return list(service.regions.values())

@router.get("/{region_id}",
            operation_id="getRegionById",
            summary="Find region by ID",
            response_model=Region,
            description="Find region by ID",
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "Region not found"},
            },
            )
async def get_region(region_id: str) -> Region:
    region = _assert_region_exists(region_id)
    logger.info(f"Get region {region_id}.")

    return region

def _assert_region_exists(region_id: str) -> Region:
    regions: RegionService = container['regions']
    region = regions.get_region(region_id)
    region_exists = region is not None

    if not region_exists:
        message = f"Region with id {region_id} does not exist."
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return region
