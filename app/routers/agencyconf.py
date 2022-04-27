import logging
from typing import List

from fastapi import APIRouter, HTTPException, status, Header, Depends

from app.models.AgencyConf import AgencyConf
from app.services.agencyconf import AgencyConfService
from app.services.config import config
from app.utils.container import container

# TODO should move this to service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agencyconf",
    tags=["agencyconf"]
)



# TODO FG can X_Api_Key be lower case?
async def verify_admin_api_key(X_Api_Key: str = Header(...)):
    if X_Api_Key != config.admin_token:
        raise HTTPException(status_code=400, detail="X_Api_Key header invalid")

    # returning without an exception means the token is good
    return None


@router.get("/",
            # TODO HB comment this in to remove from /docs
            include_in_schema=config.env != 'PROD',  # TODO FG try out
            operation_id="getAgencyIdsWhichHaveAConfiguration",
            summary="Get agency_ids which have a configuration",
            response_model=List[str],
            description="Returns the agency_ids but not the details.",
            status_code=status.HTTP_200_OK,
            )
async def get_agency_ids(admin_api_key: str = Depends(verify_admin_api_key)) -> [str]:
    agency_conf_service: AgencyConfService = container['agencyconf']

    return agency_conf_service.get_agency_ids()


tmp = config.env != 'PROD' # FG

@router.post("/",
             # TODO HB comment this in to remove from /docs
             include_in_schema=tmp,  # TODO FG try out
             operation_id="postNewAgencyConf",
             summary="Post a new AgencyConf",
             response_model=AgencyConf)
async def post_agency_conf(new_agency_conf: AgencyConf, admin_api_key: str = Depends(verify_admin_api_key)) -> AgencyConf:
    agency_conf_service: AgencyConfService = container['agencyconf']

    return agency_conf_service.add(new_agency_conf)



@router.delete("/",
               # TODO HB comment this in to remove from /docs
               # include_in_schema=False,
               operation_id="deleteToken",
               summary="Delete token of an agency. Returns true if the token for the agency existed, false if it didn't exist.",
               response_model=bool)
async def delete_token(agency_id: str, admin_token: str = Depends(verify_admin_api_key)) -> bool:
    tokens = container.get('tokens')
    token = tokens.get(agency_id)

    if token is None:
        return False
    else:
        del tokens[agency_id]

    logger.info(f"Deleted token for agency {agency_id}.")

    return True
