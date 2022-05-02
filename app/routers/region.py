import logging
import time
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from app.models.Carpool import Region
from app.routers.agencyconf import verify_admin_api_key
from app.services.regions import RegionService
from app.utils.container import container
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
            status_code=status.HTTP_200_OK,
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
            status_code=status.HTTP_200_OK,
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "Region not found"},
                # TODO note that automatic validations against the schema
                # are returned with code 422, also shown in Swagger.
                # maybe 405 is not needed?
                # 405: {"description": "Validation exception"}
            },
            )
# TODO ids should not be str, but have their own model
async def get_region(region_id: str) -> Region:
    region = _assert_region_exists(region_id)
    logger.info(f"Get region {region_id}.")

    return region

def _assert_region_exists(region_id: str) -> Region:
    regions: regionService = container['regions']
    region = regions.get_region(region_id)
    region_exists = region is not None

    if not region_exists:
        message = f"Region with id {region_id} does not exist."
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return region

@router.get("/{region_id}/gtfs", 
    summary="Return GTFS Feed for this region",
    response_description="GTFS-Feed (zip-file)",
    response_class=FileResponse,
    responses={
                status.HTTP_404_NOT_FOUND: {"description": "Region not found"},
        }
    )
async def get_file(region_id: str, user: str = Depends(verify_admin_api_key)):
    _assert_region_exists(region_id)
    return FileResponse(f'data/gtfs/amarillo.{region_id}.gtfs.zip')

@router.get("/{region_id}/gtfs-rt",
    summary="Return GTFS-RT Feed for this region",
    response_description="GTFS-RT-Feed",
    response_class=FileResponse,
    responses={
                status.HTTP_404_NOT_FOUND: {"description": "Region not found"},
        }
    )
async def get_file(region_id: str, user: str = Depends(verify_admin_api_key)):
    _assert_region_exists(region_id)
    # TODO support json
    return FileResponse(f'data/gtfs/amarillo.{region_id}.gtfsrt.pbf')