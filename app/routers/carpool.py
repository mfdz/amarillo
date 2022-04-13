import logging

from fastapi import APIRouter, Body, HTTPException, status
from datetime import datetime

from pydantic import Field

from app.models.Carpool import Carpool
from app.tests.sampledata import examples
from app.utils.container import container

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
                 status.HTTP_405_METHOD_NOT_ALLOWED: {
                     "description": "Validation exception"},
                 status.HTTP_409_CONFLICT: {
                     "description": "Carpool with this id exists already."}})
async def post_carpool(cp: Carpool = Body(...,
                                          examples=examples,
                                          )
                       ) -> Carpool:
    if cp.lastUpdated == None:
        cp.lastUpdated = datetime.now()

    exists = container['carpools'].get(cp.agency, cp.id) != None

    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Carpool with id {cp.id} exists already.")

    container['carpools'].put(cp.agency, cp.id, cp)

    print(f"Post trip {cp.agency}:{cp.id}.")

    return cp


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
            detail=f"Carpool with id {carpoolId} does not exist.")

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
