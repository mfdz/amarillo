import logging
import os
import time
from typing import List

from fastapi import APIRouter, Body, HTTPException, status, Header, Depends
from datetime import datetime

from pydantic import Field

from app.models.Carpool import Carpool, Agency
from app.models.token import Token
from app.services.carpools import CarpoolService
from app.services.config import config
from app.tests.sampledata import examples
from app.utils.container import container
from app.services.importing.ride2go import import_ride2go
# TODO should move this to service
from app.routers.carpool import store_carpool, delete_agency_carpools_older_than

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/token",
    tags=["token"]
)

async def verify_admin_token(X_Token: str = Header(...)) -> str:
    if X_Token != config.admin_token:
        raise HTTPException(status_code=400, detail="X_Token header invalid")

    # returning without an exception means the token is good
    return None


@router.get("/",
            # TODO HB comment this in to remove from /docs
            # include_in_schema=False,
            operation_id="getAgencyIdsWhichHaveAToken",
            summary="Get agency_ids which have a token",
            response_model=List[str],
            description="Returns the agency_ids but not the tokens.",
            status_code=status.HTTP_200_OK,
            )
async def get_agency_ids(admin_token: str = Depends(verify_admin_token)) -> [str]:
    tokens = container['tokens']
    agency_ids = tokens.keys()
    return list(agency_ids)

@router.post("/",
             # TODO HB comment this in to remove from /docs
             # include_in_schema=False,
             operation_id="postNewToken",
             summary="Post a new token",
             response_model=Token)
async def post_token(new_token: Token, admin_token: str = Depends(verify_admin_token)) -> Token:
    tokens = container.get('tokens')
    agency_id = new_token.agency_id
    token = new_token.token

    tokens[agency_id] = token

    logger.info(f"Added token for agency {agency_id}.")

    return new_token

@router.delete("/",
             # TODO HB comment this in to remove from /docs
             # include_in_schema=False,
             operation_id="deleteToken",
             summary="Delete token of an agency. Returns true if the token for the agency existed, false if it didn't exist.",
             response_model=bool)
async def delete_token(agency_id: str, admin_token: str = Depends(verify_admin_token)) -> bool:
    tokens = container.get('tokens')
    token = tokens.get(agency_id)

    if token is None:
        return False
    else:
        del tokens[agency_id]

    logger.info(f"Deleted token for agency {agency_id}.")

    return True
