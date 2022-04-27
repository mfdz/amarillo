import logging
from typing import List

from fastapi import APIRouter, HTTPException, status, Header, Depends

from app.models.AgencyConf import AgencyConf
from app.services.config import config
from app.utils.container import container

# TODO should move this to service
# Really? -- fg

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agencyconf",
    tags=["agencyconf"]
)

# This endpoint is not shown in PROD installations, only in development
include_in_schema = config.env != 'PROD'


# noinspection PyPep8Naming
# X_Api_Key is upper case for the OpenAPI
async def verify_admin_api_key(X_API_Key: str = Header(...)):
    if X_API_Key != config.admin_token:
        raise HTTPException(status_code=400, detail="X_API_Key header invalid")

    # returning without an exception means the token is good
    return None


@router.get("/",
            include_in_schema=include_in_schema,
            operation_id="getAgencyIdsWhichHaveAConfiguration",
            summary="Get agency_ids which have a configuration",
            response_model=List[str],
            description="Returns the agency_ids but not the details.",
            status_code=status.HTTP_200_OK)
async def get_agency_ids(admin_api_key: str = Depends(verify_admin_api_key)) -> [str]:
    return container['agencyconf'].get_agency_ids()


@router.post("/",
             include_in_schema=include_in_schema,
             operation_id="postNewAgencyConf",
             summary="Post a new AgencyConf")
async def post_agency_conf(new_agency_conf: AgencyConf,
                           admin_api_key: str = Depends(verify_admin_api_key)) -> AgencyConf:
    container['agencyconf'].add(new_agency_conf)


@router.delete("/{agency_id}",
               include_in_schema=include_in_schema,
               operation_id="deleteAgencyConf",
               summary="Delete configuration of an agency. Returns true if the token for the agency existed, false if it didn't exist.")
async def delete_agency_conf(agency_id: str, admin_api_key: str = Depends(verify_admin_api_key)):
    container['agencyconf'].delete(agency_id)
