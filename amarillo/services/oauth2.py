# OAuth2 authentication based on https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#__tabbed_4_2

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Union
import logging
import logging.config

from fastapi import Depends, HTTPException, Header, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from amarillo.models.User import User
from amarillo.services.passwords import verify_password
from amarillo.utils.container import container
from amarillo.services.agencies import AgencyService
from amarillo.services.users import UserService
from amarillo.models.Carpool import Agency

from amarillo.services.secrets import secrets

SECRET_KEY = secrets.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger("main")

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Union[str, None] = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
async def verify_optional_api_key(X_API_Key: Optional[str] = Header(None)):
    if X_API_Key == None: return None
    return await verify_api_key(X_API_Key)

def authenticate_user(user_id: str, password: str):
    user_service : UserService = container['users']
    user_conf = user_service.user_id_to_user_conf.get(user_id, None)
    if not user_conf:
        return False

    if not verify_password(password, user_conf.password):
        return False
    return user_id


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), user_from_api_key: str = Depends(verify_optional_api_key)) -> User:
    if token:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate OAuth2 credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            token_data = TokenData(user_id=user_id)
        except JWTError:
            raise credentials_exception
        user_id = token_data.user_id
        if user_id is None:
            raise credentials_exception

        user_service : UserService = container['users']
        return user_service.get_user(user_id)
    elif user_from_api_key:
        logger.info(f"API Key provided: {user_from_api_key}")
        user_service : UserService = container['users']
        return user_service.get_user(user_from_api_key)
    else:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        raise credentials_exception

def verify_permission(permission: str, user: User):

    def permissions_exception():
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User '{user.user_id}' does not have the permission '{permission}'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    #user is admin
    if "admin" in user.permissions: return

    #permission is an operation
    if ":" not in permission:
        if permission not in user.permissions:
            raise permissions_exception()

        return

    #permission is in agency:operation format
    def permission_matches(permission, user_permission):
        prescribed_agency, prescribed_operation = permission.split(":")
        given_agency, given_operation = user_permission.split(":")

        return (prescribed_agency == given_agency or given_agency == "all") and (prescribed_operation == given_operation or given_operation == "all")

    if any(permission_matches(permission, p) for p in user.permissions if ":" in p): return

    raise permissions_exception()


# noinspection PyPep8Naming
# X_API_Key is upper case for OpenAPI
async def verify_api_key(X_API_Key: str = Header(...)):
    user_service: UserService = container['users']

    return user_service.check_api_key(X_API_Key)

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    agency = authenticate_user(form_data.username, form_data.password)
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": agency}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

# TODO: eventually remove this
@router.get("/users/me/", response_model=Agency)
async def read_users_me(
    current_agency: Annotated[Agency, Depends(get_current_user)]
):
    agency_service : AgencyService = container['agencies']
    return  agency_service.get_agency(agency_id=current_agency)

# TODO: eventually remove this
@router.get("/users/me/items/")
async def read_own_items(
    current_agency: Annotated[str, Depends(get_current_user)]
):
    return [{"item_id": "Foo", "owner": current_agency}]
