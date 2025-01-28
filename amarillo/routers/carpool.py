import logging
import json
import os
import os.path
from pathlib import Path
import re
from glob import glob

from fastapi import APIRouter, Body, Header, HTTPException, status, Depends, BackgroundTasks
import requests
from requests.exceptions import ConnectionError 
from datetime import datetime

from amarillo.utils.container import container
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
    try:
        response = requests.post(f"{config.enhancer_url}", carpool.model_dump_json().encode('utf-8'))
        response.raise_for_status()
        enhanced_carpool = Carpool(**json.loads(response.content))

        folder = f'data/enhanced/{carpool.agency}'
        filename = f'{folder}/{carpool.id}.json'

        assert_folder_exists(folder)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(enhanced_carpool.model_dump_json())
    except ConnectionError:
        logger.error("Could not connect to enhancer: make sure amarillo-enhancer is running and your ENHANCER_URL environment variable is configured correctly")
    except Exception as e:
        logger.error(f"Error enhancing trip '{carpool.id}': {e}")

def enhance_missing_carpools():
    logger.info(f"Enhancing missing restored trips...")
    for agency_id in container['agencies'].agencies:
        for carpool_file_name in glob(f'data/carpool/{agency_id}/*.json'):
            carpool_id = Path(carpool_file_name).stem
            carpool = _load_carpool_if_exists(agency_id, carpool_id, folder='data/carpool')
            if not carpool:
                # logger.warning(f"Failed loading carpool {agency_id}:{carpool_id}.")
                continue

            existing_enhanced_carpool = _load_carpool_if_exists(agency_id, carpool.id, folder='data/enhanced')
            if not existing_enhanced_carpool or existing_enhanced_carpool.lastUpdated != carpool.lastUpdated:
                logger.info(f"Enhancing restored trip {carpool_file_name}")
                try:
                    enhance_trip(carpool)
                except Exception as e:
                    logger.warning("Issue during restore of carpool %s: %s", carpool_file_name, repr(e))

def carpool_exists(agency_id: str, carpool_id: str, folder: str ='data/enhanced'):
    return os.path.exists(f"{folder}/{agency_id}/{carpool_id}.json")

def _load_carpool_if_exists(agency_id: str, carpool_id: str, folder: str ='data/enhanced'):
    if carpool_exists(agency_id, carpool_id, folder):
        try:
            return _load_carpool_from_path(f"{folder}/{agency_id}/{carpool_id}.json")
        except Exception as e:
            # An error on restore could be caused by model changes, 
            # in such a case, it need's to be recreated
            logger.warning(f"Could not restore trip {folder}/{agency_id}/{carpool_id}.json: {repr(e)}")

    return None


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


async def load_carpool(agency_id, carpool_id, folder: str ='data/carpool') -> Carpool:
    return _load_carpool_from_path(f'{folder}/{agency_id}/{carpool_id}.json')

def _load_carpool_from_path(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        dict = json.load(f)
        carpool = Carpool(**dict)
    return carpool

async def save_carpool(carpool, folder: str = 'data/carpool'):
    with open(f'{folder}/{carpool.agency}/{carpool.id}.json', 'w', encoding='utf-8') as f:
        f.write(carpool.json())


async def assert_agency_exists(agency_id: str):
    agency_exists = os.path.exists(f"data/agency/{agency_id}.json")
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
