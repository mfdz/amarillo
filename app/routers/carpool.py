import logging
import json
import os
import os.path
import re
from glob import glob

from fastapi import APIRouter, Body, Header, HTTPException, status, Depends
from datetime import datetime

from app.models.Carpool import Carpool
from app.routers.agencyconf import verify_api_key, verify_permission_for_same_agency_or_admin
from app.tests.sampledata import examples


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/carpool",
    tags=["carpool"]
)


@router.put("/",
            operation_id="updatecarpool",
            summary="Update an existing carpool",
            response_model=Carpool,
            description="Carpool object that should be updated",
            status_code=status.HTTP_202_ACCEPTED,
            # TODO next to the status codes are "Links". There is nothing shown now.
            # Either show something there, or hide the Links, or do nothing.
            responses={400: {"description": "Invalid"},
                       404: {"description": "Agency or carpool not found"},
                       # TODO note that automatic validations against the schema
                       # are returned with code 422, also shown in Swagger.
                       # maybe 405 is not needed?
                       405: {"description": "Validation exception"}},
            )
async def put_carpool(carpool: Carpool = Body(..., examples=examples),
                      requesting_agency_id: str = Depends(verify_api_key)) -> Carpool:
    await verify_permission_for_same_agency_or_admin(carpool.agency, requesting_agency_id)

    logger.info(f"Put trip {carpool.agency}:{carpool.id}.")
    await assert_agency_exists(carpool.agency)
    await assert_carpool_exists(carpool.agency, carpool.id)

    await set_lastUpdated_if_unset(carpool)

    await save_carpool(carpool)

    return carpool


@router.post("/",
             operation_id="addcarpool",
             summary="Add a new carpool",
             description="Carpool object to be created",
             response_model=Carpool,
             responses={
                 status.HTTP_200_OK: {
                     "description": "Carpool created"},
                 # TODO note that automatic validations against the schema
                 # are returned with code 422, also shown in Swagger.
                 # maybe 405 is not needed?
                 status.HTTP_404_NOT_FOUND: {
                     "description": "Agency does not exist"},
                 status.HTTP_405_METHOD_NOT_ALLOWED: {
                     "description": "Validation exception"},
                 status.HTTP_409_CONFLICT: {
                     "description": "Carpool with this id exists already."}})
async def post_carpool(carpool: Carpool = Body(..., examples=examples),
                       requesting_agency_id: str = Depends(verify_api_key)) -> Carpool:
    await verify_permission_for_same_agency_or_admin(carpool.agency, requesting_agency_id)

    logger.info(f"POST trip {carpool.agency}:{carpool.id}.")
    # TODO DRY, implementation same as PUT
    await assert_agency_exists(carpool.agency)
    await assert_carpool_does_not_exist(carpool.agency, carpool.id)

    await set_lastUpdated_if_unset(carpool)

    await save_carpool(carpool)

    return carpool
    

@router.get("/{agencyId}/{carpoolId}",
            operation_id="getcarpoolById",
            summary="Find carpool by ID",
            response_model=Carpool,
            description="Find carpool by ID",
            status_code=status.HTTP_200_OK,
            # TODO next to the status codes are "Links". There is nothing shown now.
            # Either show something there, or hide the Links, or do nothing.
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "Carpool not found"},
                # TODO note that automatic validations against the schema
                # are returned with code 422, also shown in Swagger.
                # maybe 405 is not needed?
                # 405: {"description": "Validation exception"}
            },
            )
async def get_carpool(agencyId: str, carpoolId: str, api_key: str = Depends(verify_api_key)) -> Carpool:
    logger.info(f"Get trip {agencyId}:{carpoolId}.")
    await assert_agency_exists(agencyId)
    await assert_carpool_exists(agencyId, carpoolId)

    carpool = await load_carpool(agencyId, carpoolId)

    return carpool


@router.delete("/{agencyId}/{carpoolId}",
               operation_id="deletecarpool",
               summary="Deletes a carpool",
               description="carpool id to delete",
               status_code=status.HTTP_200_OK,
               # TODO next to the status codes are "Links". There is nothing shown now.
               # Either show something there, or hide the Links, or do nothing.
               responses={
                   status.HTTP_404_NOT_FOUND: {
                       "description": "Carpool not found"},
                   # TODO note that automatic validations against the schema
                   # are returned with code 422, also shown in Swagger.
                   # maybe 405 is not needed?
                   # 405: {"description": "Validation exception"}
               },
               )
async def delete_carpool(agencyId: str, carpoolId: str, requesting_agency_id: str = Depends(verify_api_key)):
    await verify_permission_for_same_agency_or_admin(agencyId, requesting_agency_id)

    logger.info(f"Delete trip {agencyId}:{carpoolId}.")
    await assert_agency_exists(agencyId)
    await assert_carpool_exists(agencyId, carpoolId)
    
    return await _delete_carpool(agencyId, carpoolId)

async def _delete_carpool(agencyId: str, carpoolId: str):
    logger.info(f"Delete carpool {agencyId}:{carpoolId}.")
    cp = await load_carpool(agencyId, carpoolId)
    logger.info(f"Loaded carpool {agencyId}:{carpoolId}.")
    # load and store, to receive pyinotify events and have file timestamp updated
    await save_carpool(cp, 'data/trash')
    logger.info(f"Saved carpool {agencyId}:{carpoolId} in trash.")
    os.remove(f"data/carpool/{agencyId}/{carpoolId}.json")

async def store_carpool(carpool: Carpool) -> Carpool:
    await set_lastUpdated_if_unset(carpool)
    await save_carpool(carpool)

    return carpool

async def set_lastUpdated_if_unset(carpool):
    if carpool.lastUpdated is None:
        carpool.lastUpdated = datetime.now()


async def load_carpool(agencyId, carpoolId) -> Carpool:
    with open(f'data/carpool/{agencyId}/{carpoolId}.json', 'r', encoding='utf-8') as f:
        dict = json.load(f)
        carpool = Carpool(**dict)
    return carpool


async def save_carpool(carpool, folder: str = 'data/carpool'):
    with open(f'{folder}/{carpool.agency}/{carpool.id}.json', 'w', encoding='utf-8') as f:
        f.write(carpool.json())


async def assert_agency_exists(agency_id: str):
    agency_exists = os.path.exists(f"conf/agency/{agency_id}.json")
    if not agency_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agency with id {agency_id} does not exist.")


async def assert_carpool_exists(agency_id: str, carpool_id: str):
    carpool_exists = os.path.exists(f"data/carpool/{agency_id}/{carpool_id}.json")
    if not carpool_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Carpool with id {carpool_id} for agency {agency_id} not found")


async def assert_carpool_does_not_exist(agency_id: str, carpool_id: str):
    carpool_exists = os.path.exists(f"data/carpool/{agency_id}/{carpool_id}.json")
    if carpool_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Carpool with id {carpool_id} exists already.")

async def delete_agency_carpools_older_than(agencyId, timestamp):
    for carpool_file_name in glob(f'data/carpool/{agencyId}/*.json'):
        if os.path.getctime(carpool_file_name) < timestamp:
            m = re.search(r'([a-zA-Z0-9_-]+)\.json$', carpool_file_name)
            await _delete_carpool(agencyId, m[1])
