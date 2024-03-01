# OAuth2 authentication based on https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#__tabbed_4_2

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Union
import logging

from fastapi import Depends, HTTPException, Header, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from amarillo.services.passwords import verify_password
from amarillo.utils.container import container
from amarillo.services.agencies import AgencyService
from amarillo.services.agencyconf import AgencyConfService
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
    agency_id: Union[str, None] = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
async def verify_optional_api_key(X_API_Key: Optional[str] = Header(None)):
    if X_API_Key == None: return None
    return await verify_api_key(X_API_Key)

def authenticate_agency(agency_id: str, password: str):
    agency_conf_service : AgencyConfService = container['agencyconf']
    agency_conf = agency_conf_service.agency_id_to_agency_conf.get(agency_id, None)
    if not agency_conf:
        return False

    agency_password = agency_conf.password
    if not verify_password(password, agency_password):
        return False
    return agency_id


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_agency(token: str = Depends(oauth2_scheme), agency_from_api_key: str = Depends(verify_optional_api_key)):
    if token:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate OAuth2 credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            agency_id: str = payload.get("sub")
            if agency_id is None:
                raise credentials_exception
            token_data = TokenData(agency_id=agency_id)
        except JWTError:
            raise credentials_exception
        user = token_data.agency_id
        if user is None:
            raise credentials_exception
        return user
    elif agency_from_api_key:
        logger.info(f"API Key provided: {agency_from_api_key}")
        return agency_from_api_key
    else:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        raise credentials_exception


async def verify_admin(agency: str = Depends(get_current_agency)):
    #TODO: maybe separate error for when admin credentials are invalid vs valid but not admin?
    if(agency != "admin"):
        message="This operation requires admin privileges"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return "admin"


# noinspection PyPep8Naming
# X_API_Key is upper case for OpenAPI
async def verify_api_key(X_API_Key: str = Header(...)):
    agency_conf_service: AgencyConfService = container['agencyconf']

    return agency_conf_service.check_api_key(X_API_Key)

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    agency = authenticate_agency(form_data.username, form_data.password)
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
    current_agency: Annotated[Agency, Depends(get_current_agency)]
):
    agency_service : AgencyService = container['agencies']
    return  agency_service.get_agency(agency_id=current_agency)

# TODO: eventually remove this
@router.get("/users/me/items/")
async def read_own_items(
    current_agency: Annotated[str, Depends(get_current_agency)]
):
    return [{"item_id": "Foo", "owner": current_agency}]
