import logging
from typing import List

from fastapi import APIRouter, HTTPException, status, Header, Depends

from amarillo.models.AgencyConf import AgencyConf
from amarillo.services.agencyconf import AgencyConfService
from amarillo.services.config import config
from amarillo.utils.container import container

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agencyconf",
    tags=["agencyconf"]
)

# This endpoint is not shown in PROD installations, only in development
# TODO make this an explicit config option
include_in_schema = config.env != 'PROD'


# noinspection PyPep8Naming
# X_API_Key is upper case for OpenAPI
async def verify_admin_api_key(X_API_Key: str = Header(...)):
    if X_API_Key != config.admin_token:
        message="X-API-Key header invalid"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return "admin"


# noinspection PyPep8Naming
# X_API_Key is upper case for OpenAPI
async def verify_api_key(X_API_Key: str = Header(...)):
    agency_conf_service: AgencyConfService = container['agencyconf']

    agency_id = agency_conf_service.check_api_key(X_API_Key)
    logger.info(f"API key used: {agency_id}")
    return agency_id

# TODO Return code 403 Unauthoized (in response_status_codes as well...)
async def verify_permission_for_same_agency_or_admin(agency_id_in_path_or_body, agency_id_from_api_key):
    """Verifies that an agency is accessing something it owns or the user is admin

    The agency_id is part of some paths, or when not in the path it is in the body, e.g. in PUT /carpool.

    This function encapsulates the formula 'working with own stuff, or admin'.
    """
    is_permitted = agency_id_in_path_or_body == agency_id_from_api_key or agency_id_from_api_key == "admin"

    if not is_permitted:
        message = f"Working with {agency_id_in_path_or_body} resources is not permitted for {agency_id_from_api_key}."
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/",
            include_in_schema=include_in_schema,
            operation_id="getAgencyIdsWhichHaveAConfiguration",
            summary="Get agency_ids which have a configuration",
            response_model=List[str],
            description="Returns the agency_ids but not the details.",
            status_code=status.HTTP_200_OK)
async def get_agency_ids(admin_api_key: str = Depends(verify_api_key)) -> [str]:
    return container['agencyconf'].get_agency_ids()


@router.post("/",
             include_in_schema=include_in_schema,
             operation_id="postNewAgencyConf",
             summary="Post a new AgencyConf")
async def post_agency_conf(agency_conf: AgencyConf, admin_api_key: str = Depends(verify_admin_api_key)):
    agency_conf_service: AgencyConfService = container['agencyconf']
    agency_conf_service.add(agency_conf)

# TODO 400->403
@router.delete("/{agency_id}",
               include_in_schema=include_in_schema,
               operation_id="deleteAgencyConf",
               status_code=status.HTTP_200_OK,
               summary="Delete configuration of an agency. Returns true if the token for the agency existed, "
                       "false if it didn't exist."
               )
async def delete_agency_conf(agency_id: str, requesting_agency_id: str = Depends(verify_api_key)):
    agency_may_delete_own = requesting_agency_id == agency_id
    admin_may_delete_everything = requesting_agency_id == "admin"
    is_permitted = agency_may_delete_own or admin_may_delete_everything

    if not is_permitted:
        message = f"The API key for {requesting_agency_id} can not delete the configuration for {agency_id}"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    agency_conf_service: AgencyConfService = container['agencyconf']

    agency_exists = agency_id in agency_conf_service.get_agency_ids()

    if not agency_exists:
        message = f"No config for {agency_id}"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    agency_conf_service.delete(agency_id)
