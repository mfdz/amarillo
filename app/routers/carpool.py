import logging
import os.path
from typing import List

from fastapi import APIRouter, Body, HTTPException, status
from datetime import datetime

from pydantic import Field

from app.models.Carpool import Carpool
from app.tests.sampledata import examples
from app.utils.container import container
from app.services.importing.ride2go import import_ride2go

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
                       404: {"description": "Carpool not found"},
                       # TODO note that automatic validations against the schema
                       # are returned with code 422, also shown in Swagger.
                       # maybe 405 is not needed?
                       405: {"description": "Validation exception"}},
            )
async def put_carpool(cp: Carpool = Body(..., examples=examples)
                      ) -> Carpool:
    exists = container['carpools'].get(cp.agency, cp.id) != None

    if not exists:
        raise HTTPException(
            status_code=404,
            detail=f"Carpool with id {cp.id} for agency {cp.agency} not found")

    if cp.lastUpdated == None:
        cp.lastUpdated = datetime.now()

    container['carpools'].put(cp.agency, cp.id, cp)

    print(f"Put trip {cp.agency}:{cp.id}.")

    return cp


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
async def post_carpool(carpool: Carpool = Body(...,
                                               examples=examples,
                                               )
                       ) -> Carpool:
    agency_exists = os.path.exists(f"data/agency/{carpool.agency}.json")

    if not agency_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agency with id {carpool.agency} does not exist.")

    if carpool.lastUpdated is None:
        carpool.lastUpdated = datetime.now()

    carpool_exists = os.path.exists(f"data/carpool/{carpool.agency}/{carpool.id}.json")

    if carpool_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Carpool with id {carpool.id} exists already.")

    with open(f'data/carpool/{carpool.agency}/{carpool.id}.json', 'w', encoding='utf-8') as f:
        f.write(carpool.json())

    logger.info("POST trip {carpool.agency}:{carpool.id}.")

    return carpool


@router.get("/import",
            include_in_schema=False,
            status_code=status.HTTP_200_OK,
            responses={
                status.HTTP_500_INTERNAL_SERVER_ERROR:
                    {"description": "Import error"},
            },
            )
# TODO pass in agencyId: str
async def import_() -> List[Carpool]:
    carpools = container["carpools"]
    try:
        ride2go_carpools = import_ride2go()

        [carpools.put(cp.agency, cp.id, cp) for cp in ride2go_carpools]

        return ride2go_carpools

    except BaseException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong during importing from ride2go. {e}")


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
async def get_carpool(agencyId: str, carpoolId: str) -> Carpool:
    exists = container['carpools'].get(agencyId, carpoolId) != None

    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Carpool with agency {agencyId} and id {carpoolId} does not exist.")

    print(f"Get trip {agencyId}:{carpoolId}.")

    return container['carpools'].get(agencyId, carpoolId)


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
async def delete_carpool(agencyId: str, carpoolId: str):
    exists = container['carpools'].get(agencyId, carpoolId) != None

    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Carpool with id {carpoolId} does not exist.")

    container['carpools'].delete(agencyId, carpoolId)

    print(f"Delete trip {agencyId}:{carpoolId}.")

    return "deleted"
