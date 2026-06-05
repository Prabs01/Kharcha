from datetime import datetime, timedelta, UTC

import jwt
from fastapi.security import OAuth2PasswordBearer

from pwdlib import PasswordHash

from app.config import settings

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

def verify_access_token(token: str) -> dict | None:
    """Verifies a JWT access token and returns the decoded data if valid."""
    try:
        payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[settings.algorithm])
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")
         