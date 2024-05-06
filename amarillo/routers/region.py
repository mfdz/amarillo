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
                status.HTTP_400_BAD_REQUEST: {"description": "Bad request, e.g. because format is not supported, i.e. neither protobuf nor json."}
        }
    )
async def get_file(region_id: str, format: str = 'protobuf', user: str = Depends(verify_admin_api_key)):
    _assert_region_exists(region_id)
    if format == 'json':
        return FileResponse(f'data/gtfs/amarillo.{region_id}.gtfsrt.json')
    elif format == 'protobuf':
        return FileResponse(f'data/gtfs/amarillo.{region_id}.gtfsrt.pbf')
    else:
        message = "Specified format is not supported, i.e. neither protobuf nor json."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
