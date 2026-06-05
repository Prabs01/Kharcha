from fastapi import APIRouter, HTTPException, Query, Depends
import app.models as models
from sqlmodel import select, func
from typing import Annotated

from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import (hash_password, verify_password, create_access_token, verify_access_token, oauth2_scheme)
from app.config import settings


router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post(path='/', response_model = models.UserRead)
async def create_user(user: models.UserCreate, session:models.SessionDep):
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

@router.post("/token", response_model=models.Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: models.SessionDep): #Depends() is used to declare dependencies for the endpoint. In this case, it is used to get the form data for the login and the database session.
    user = session.exec(select(models.User).where(func.lower(models.User.email) == form_data.username.lower())).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

    return models.Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=models.UserRead)
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: models.SessionDep): #oatuh2_scheme is only for Swagger UI, it tells when you clicj on the "Authorize" button got to the "/users/token" endpoint to get the token and then use that token for the endpoints that require authentication. Depends() is used to declare dependencies for the endpoint. In this case, it is used to get the token from the request and the database session.
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get('/', response_model = list[models.UserRead])
async def read_users(
    session: models.SessionDep,
    offset: int = 0,
    limit: Annotated[int , Query(ge=1,le=100)] = 100,
):
    users = session.exec(select(models.User).offset(offset).limit(limit)).all()
    return users

@router.get(path="/{user_id}", response_model = models.UserRead)
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