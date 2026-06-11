from fastapi import APIRouter, HTTPException, Query, Depends
import app.models as models
import app.schemas as schemas
from sqlmodel import select, func
from typing import Annotated

from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

import logging

from app.auth import (
    CurrentUser,
    hash_password,
    verify_password,
    create_access_token,
    verify_google_token,
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post(path='/', response_model = schemas.UserRead)
async def create_user(user: schemas.UserCreate, session:models.SessionDep):
    db_user = models.User(
        name = user.name,
        email = user.email.lower() ,
        hashed_password= hash_password(user.password) #need to be hashed later
    )

    if session.exec(select(models.User).where(func.lower(models.User.email) == user.email.lower())).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    if db_user.id is None:
        raise HTTPException(status_code=500, detail="Failed to create user")

    
    return db_user

@router.post("/google")
async def google_login(payload: schemas.GoogleLogin, session: models.SessionDep):
    logging.info("Received Google login request with credential: %s", payload.token)

    user_info = verify_google_token(payload.token)

    email = user_info.get("email")
    name = user_info.get("name")
    
    user = session.exec(select(models.User).where(models.User.email == email)).first()

    if not user:
        if not email or not name:
            raise HTTPException(status_code=400, detail="Google token is missing required user information")
        user = models.User(name=name, email=email, hashed_password=None, is_google_account=True)
        session.add(user)
        session.commit()
        session.refresh(user)
    
    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=schemas.Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: models.SessionDep): #Depends() is used to declare dependencies for the endpoint. In this case, it is used to get the form data for the login and the database session.
    user = session.exec(select(models.User).where(func.lower(models.User.email) == form_data.username.lower())).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if user.is_google_account:
        raise HTTPException(status_code=400, detail="Please log in with Google")
    if user.hashed_password is None:
        raise HTTPException(status_code=400, detail="User signed up with Google, no password set. Please log in with Google.")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

    return schemas.Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=schemas.UserRead)
async def read_current_user(current_user: CurrentUser):
    return current_user


@router.get('/', response_model = list[schemas.UserRead])
async def read_users(
    session: models.SessionDep,
    offset: int = 0,
    limit: Annotated[int , Query(ge=1,le=100)] = 100,
):
    users = session.exec(select(models.User).offset(offset).limit(limit)).all()
    return users

@router.get(path="/{user_id}", response_model = schemas.UserRead)
async def read_user(user_id:int, session: models.SessionDep):
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete(path="/{user_id}")
async def delete_user(user_id:int, session:models.SessionDep):
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok" : True}