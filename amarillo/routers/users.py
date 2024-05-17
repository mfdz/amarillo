import logging
from typing import List

from fastapi import APIRouter, HTTPException, status, Header, Depends

from amarillo.models.User import User
from amarillo.services.users import UserService
from amarillo.services.oauth2 import get_current_agency, verify_admin
from amarillo.services.config import config
from amarillo.utils.container import container

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# This endpoint is not shown in PROD installations, only in development
# TODO make this an explicit config option
include_in_schema = config.env != 'PROD'


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
            operation_id="getUserIdsWhichHaveAConfiguration",
            summary="Get user which have a configuration",
            response_model=List[str],
            description="Returns the user_ids but not the details.",
            status_code=status.HTTP_200_OK)
async def get_user_ids(admin_api_key: str = Depends(get_current_agency)) -> [str]:
    return container['users'].get_user_ids()


@router.post("/",
             include_in_schema=include_in_schema,
             operation_id="postNewUserConf",
             summary="Post a new User")
async def post_user_conf(user_conf: User, admin_api_key: str = Depends(verify_admin)):
    user_service: UserService = container['users']
    user_service.add(user_conf)

# TODO 400->403
@router.delete("/{user_id}",
               include_in_schema=include_in_schema,
               operation_id="deleteUser",
               status_code=status.HTTP_200_OK,
               summary="Delete configuration of a user. Returns true if the token for the user existed, "
                       "false if it didn't exist."
               )
async def delete_user(user_id: str, requesting_user_id: str = Depends(get_current_agency)):
    agency_may_delete_own = requesting_user_id == user_id
    admin_may_delete_everything = requesting_user_id == "admin"
    is_permitted = agency_may_delete_own or admin_may_delete_everything

    if not is_permitted:
        message = f"The API key for {requesting_user_id} can not delete the configuration for {user_id}"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    user_service: UserService = container['users']

    agency_exists = user_id in user_service.get_user_ids()

    if not agency_exists:
        message = f"No config for {user_id}"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    user_service.delete(user_id)
