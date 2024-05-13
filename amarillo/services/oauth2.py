# OAuth2 authentication based on https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#__tabbed_4_2

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Union
import logging

from fastapi import Depends, HTTPException, Header, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from amarillo.routers.agencyconf import verify_api_key

from amarillo.services.config import config

SECRET_KEY = config.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger("main")

# TODO: use agencyconf for saving the hashed password
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    },
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    agency_id: Union[str, None] = None


class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
async def verify_optional_api_key(X_API_Key: Optional[str] = Header(None)):
    if X_API_Key == None: return None
    return await verify_api_key(X_API_Key)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

def get_agency(db, agency_id: str):
    if agency_id in db:
        user_dict = db[agency_id]
        return UserInDB(**user_dict)

def authenticate_agency(fake_db, username: str, password: str):
    agency = get_agency(fake_db, username)
    if not agency:
        return False
    if not verify_password(password, agency.hashed_password):
        return False
    return agency


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

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    agency = authenticate_agency(fake_users_db, form_data.username, form_data.password)
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": agency.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

# TODO: eventually remove this
@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_agency: Annotated[User, Depends(get_current_agency)]
):
    return  get_agency(fake_users_db, agency_id=current_agency)

# TODO: eventually remove this
@router.get("/users/me/items/")
async def read_own_items(
    current_agency: Annotated[User, Depends(get_current_agency)]
):
    return [{"item_id": "Foo", "owner": current_agency}]
