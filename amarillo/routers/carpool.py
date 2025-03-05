import logging
import json
import os
import os.path
import re
from glob import glob

from fastapi import APIRouter, Body, Header, HTTPException, status, Depends
from datetime import datetime

from amarillo.models.Carpool import Carpool
from amarillo.routers.agencyconf import verify_api_key, verify_permission_for_same_agency_or_admin
from amarillo.tests.sampledata import examples
from amarillo.stores.filebasedstore import FileBasedStore


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/carpool",
    tags=["carpool"]
)

store = FileBasedStore()


examples = [
    {
        "id": "1235",
        "agency_id": "mfdz",
        "deeplink": "http://mfdz.de",
        "stops": [
            {
                "id": "de:08416:10701",
                "name": "Tübingen Hauptbahnhof",
                "lat": 48.51391,
                "lon": 9.0573,
                "departureTime": "08:00",
            },
            {
                "id": "de:08111:2594",
                "name": "Degerloch Albstraße",
                "lat": 48.746419,
                "lon": 9.163373,
                "arrivalTime": "08:34",
            },
        ],
        "departureTime": "08:00",
        "departureDate": "2025-03-30",
        "lastUpdated": "2025-03-03T18:22:00+00:00",
        "path": {"type": "LineString", "coordinates": [[48.51391, 9.0573], [48.64632, 9.23224], [48.746419, 9.163373]]},
    },
    {
        "id": "1234",
        "agency_id": "mfdz",
        "deeplink": "http://mfdz.de",
        "stops": [
            {"id": "de:12073:900340137::2", "name": "ABC", "lat": 45, "lon": 9},
            {"id": "de:12073:900340137::3", "name": "XYZ", "lat": 45, "lon": 9},
        ],
        "departureTime": "12:34",
        "departureDate": "2022-03-30",
        "lastUpdated": "2022-03-30T12:34:00+00:00",
    },
]


@router.post(
    "/",
    operation_id="addcarpool",
    summary="Add a new or update existing carpool",
    description="Carpool object to be created or updated",
    response_model=Carpool,
    responses={
                 status.HTTP_404_NOT_FOUND: {
                     "description": "Agency does not exist"},
                 
                })
async def post_carpool(carpool: Carpool = Body(..., examples=examples),
                       requesting_agency_id: str = Depends(verify_api_key)) -> Carpool:
    await verify_permission_for_same_agency_or_admin(carpool.agency, requesting_agency_id)

    logger.info(f"POST trip {carpool.agency}:{carpool.id}.")
    await _assert_agency_exists(carpool.agency)

    await store.store_carpool(carpool)

    return carpool

# TODO 403
@router.get("/{agency_id}/{carpool_id}",
    operation_id="getcarpoolById",
    summary="Find carpool by ID",
    response_model=Carpool,
    description="Find carpool by ID",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Carpool not found"},
    },
)
async def get_carpool(agency_id: str, carpool_id: str, api_key: str = Depends(verify_api_key)) -> Carpool:
    logger.info(f"Get trip {agency_id}:{carpool_id}.")
    await _assert_agency_exists(agency_id)
    await _assert_carpool_exists(agency_id, carpool_id)

    carpool = await store.load_carpool(agency_id, carpool_id)

    return carpool


@router.delete("/{agency_id}/{carpool_id}",
    operation_id="deletecarpool",
    summary="Deletes a carpool",
    description="Carpool id to delete",
    responses={
                   status.HTTP_404_NOT_FOUND: {
                       "description": "Carpool or agency not found"},
    },
)
async def delete_carpool(agency_id: str, carpool_id: str, requesting_agency_id: str = Depends(verify_api_key)):
    await verify_permission_for_same_agency_or_admin(agency_id, requesting_agency_id)

    logger.info(f"Delete trip {agency_id}:{carpool_id}.")
    await _assert_agency_exists(agency_id)
    await _assert_carpool_exists(agency_id, carpool_id)

    return await store.delete_carpool(agency_id, carpool_id)


async def set_lastUpdated_if_unset(carpool):
    if carpool.lastUpdated is None:
        carpool.lastUpdated = datetime.now()


async def _assert_agency_exists(agency_id: str):
    if not store.does_agency_exist(agency_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agency with id {agency_id} does not exist.")


async def _assert_carpool_exists(agency_id: str, carpool_id: str):
    if not store.does_carpool_exist(agency_id, carpool_id):
        raise HTTPException(status_code=404, detail=f"Carpool with id {carpool_id} for agency {agency_id} not found")
