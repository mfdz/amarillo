import logging
from typing import List

from fastapi import APIRouter, HTTPException, status, Header, Depends

from amarillo.models.User import User
from amarillo.services.users import UserService
from amarillo.services.oauth2 import get_current_user, verify_permission
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


@router.get("/",
            include_in_schema=include_in_schema,
            operation_id="getUserIdsWhichHaveAConfiguration",
            summary="Get user which have a configuration",
            response_model=List[str],
            description="Returns the user_ids but not the details.",
            status_code=status.HTTP_200_OK)
async def get_user_ids(requesting_user: User = Depends(get_current_user)) -> [str]:
    return container['users'].get_user_ids()


@router.post("/",
             include_in_schema=include_in_schema,
             operation_id="postNewUserConf",
             summary="Post a new User")
async def post_user_conf(user_conf: User, requesting_user: User = Depends(get_current_user)):
    verify_permission("admin", requesting_user)
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
async def delete_user(user_id: str, requesting_user: User = Depends(get_current_user)):
    user_may_delete_own = requesting_user.user_id == user_id
    admin_may_delete_everything = "admin" in requesting_user.permissions
    is_permitted = user_may_delete_own or admin_may_delete_everything

    if not is_permitted:
        message = f"User '{requesting_user.user_id} can not delete the configuration for {user_id}"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    user_service: UserService = container['users']

    agency_exists = user_id in user_service.get_user_ids()

    if not agency_exists:
        message = f"No config for {user_id}"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    user_service.delete(user_id)
