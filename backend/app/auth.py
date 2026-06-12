from datetime import datetime, timedelta, UTC
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from pwdlib import PasswordHash

import app.models as models
import app.db as db
from app.config import settings

from google.oauth2 import id_token
from google.auth.transport import requests

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token") #only tells the Swagger UI where to go to get the token when you click on the "Authorize" button. It does not actually handle the authentication, that is done in the "/users/token" endpoint.

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Creates a JWT access token with the given data and expiration time."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key.get_secret_value(), algorithm=settings.algorithm)
    return encoded_jwt

def verify_access_token(token: str) -> str | None:
    """Verifies a JWT access token and returns the user id from `sub` if valid."""
    try:
        payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[settings.algorithm])
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None

def verify_google_token(token: str) -> dict:
    """Verifies a Google ID token and returns the user info if valid."""
    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request(), settings.google_client_id)
        return id_info
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: db.SessionDep,
) -> models.User:
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = session.get(models.User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]