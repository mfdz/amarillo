import logging
import os
from typing import List

from fastapi import APIRouter, Body, HTTPException, status
from datetime import datetime

from pydantic import Field

from app.models.Carpool import Carpool, Agency
from app.services.carpools import CarpoolService
from app.tests.sampledata import examples
from app.utils.container import container
from app.services.importing.ride2go import import_ride2go

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agency",
    tags=["agency"]
)


@router.get("/{agencyId}",
            operation_id="getAgencyById",
            summary="Find agency by ID",
            response_model=Agency,
            description="Find agency by ID",
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
async def get_agency(agency_id: str) -> Agency:
    carpools: CarpoolService = container['carpools']

    agency = carpools.get_agency(agency_id)

    exists = agency is not None

    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agency with id {agency_id} does not exist.")

    print(f"Get agency {agency_id}.")

    return agency
