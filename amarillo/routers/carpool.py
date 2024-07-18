import logging
import json
import os
import os.path
import re
from glob import glob

from fastapi import APIRouter, Body, Header, HTTPException, status, Depends, BackgroundTasks
import requests
from datetime import datetime

from amarillo.models.Carpool import Carpool
from amarillo.routers.agencyconf import verify_api_key, verify_permission_for_same_agency_or_admin
from amarillo.tests.sampledata import examples
from amarillo.services.hooks import run_on_create, run_on_delete
from amarillo.services.config import config
from amarillo.utils.utils import assert_folder_exists

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/carpool",
    tags=["carpool"]
)

#TODO: housekeeping for outdated trips

def enhance_trip(carpool: Carpool):
    response = requests.post(f"{config.enhancer_url}", carpool.model_dump_json())
    enhanced_carpool = Carpool(**json.loads(response.content))

    folder = f'data/enhanced/{carpool.agency}'
    filename = f'{folder}/{carpool.id}.json'

    assert_folder_exists(folder)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(enhanced_carpool.model_dump_json())

@router.post("/",
             operation_id="addcarpool",
             summary="Add a new or update existing carpool",
             description="Carpool object to be created or updated",
             response_model=Carpool,
             response_model_exclude_none=True,
             responses={
                 status.HTTP_404_NOT_FOUND: {
                     "description": "Agency does not exist"},
                 
                })
async def post_carpool(background_tasks: BackgroundTasks, carpool: Carpool = Body(..., examples=examples),
                       requesting_agency_id: str = Depends(verify_api_key)) -> Carpool:
    await verify_permission_for_same_agency_or_admin(carpool.agency, requesting_agency_id)

    background_tasks.add_task(run_on_create, carpool)

    logger.info(f"POST trip {carpool.agency}:{carpool.id}.")
    await assert_agency_exists(carpool.agency)

    await store_carpool(carpool)

    background_tasks.add_task(enhance_trip, carpool)

    return carpool
    
# TODO 403
@router.get("/{agency_id}/{carpool_id}",
            operation_id="getcarpoolById",
            summary="Find carpool by ID",
            response_model=Carpool,
            response_model_exclude_none=True,
            description="Find carpool by ID",
            responses={
                status.HTTP_404_NOT_FOUND: {"description": "Carpool not found"},
            },
            )
async def get_carpool(agency_id: str, carpool_id: str, api_key: str = Depends(verify_api_key)) -> Carpool:
    logger.info(f"Get trip {agency_id}:{carpool_id}.")
    await assert_agency_exists(agency_id)
    await assert_carpool_exists(agency_id, carpool_id)

    carpool = await load_carpool(agency_id, carpool_id)

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
async def delete_carpool(background_tasks: BackgroundTasks, agency_id: str, carpool_id: str, requesting_agency_id: str = Depends(verify_api_key)):
    await verify_permission_for_same_agency_or_admin(agency_id, requesting_agency_id)

    logger.info(f"Delete trip {agency_id}:{carpool_id}.")
    await assert_agency_exists(agency_id)
    await assert_carpool_exists(agency_id, carpool_id)
    cp = await load_carpool(agency_id, carpool_id)
    background_tasks.add_task(run_on_delete, cp)
    
    return await _delete_carpool(agency_id, carpool_id)

async def _delete_carpool(agency_id: str, carpool_id: str):
    logger.info(f"Delete carpool {agency_id}:{carpool_id}.")
    cp = await load_carpool(agency_id, carpool_id)
    logger.info(f"Loaded carpool {agency_id}:{carpool_id}.")
    # load and store, to receive pyinotify events and have file timestamp updated
    await save_carpool(cp, 'data/trash')
    logger.info(f"Saved carpool {agency_id}:{carpool_id} in trash.")
    try:
        os.remove(f"data/carpool/{agency_id}/{carpool_id}.json")
        os.remove(f"data/enhanced/{agency_id}/{carpool_id}.json", )
    except FileNotFoundError:
        pass
    

async def store_carpool(carpool: Carpool) -> Carpool:
    carpool_exists = os.path.exists(f"data/carpool/{carpool.agency}/{carpool.id}.json")

    await set_lastUpdated_if_unset(carpool)
    await save_carpool(carpool)

    return carpool

async def set_lastUpdated_if_unset(carpool):
    if carpool.lastUpdated is None:
        carpool.lastUpdated = datetime.now()


async def load_carpool(agency_id, carpool_id) -> Carpool:
    with open(f'data/carpool/{agency_id}/{carpool_id}.json', 'r', encoding='utf-8') as f:
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


async def delete_agency_carpools_older_than(agency_id, timestamp):
    for carpool_file_name in glob(f'data/carpool/{agency_id}/*.json'):
        if os.path.getmtime(carpool_file_name) < timestamp:
            m = re.search(r'([a-zA-Z0-9_-]+)\.json$', carpool_file_name)
            # TODO log deletion
            cp = await load_carpool(agency_id, m[1])
            run_on_delete(cp)
            await _delete_carpool(agency_id, m[1])
