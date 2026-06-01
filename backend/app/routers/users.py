from fastapi import APIRouter, HTTPException, Query
import app.models as models
from sqlmodel import select
from typing import Annotated

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post(path='/', response_model = models.UserRead)
async def create_user(user: models.UserCreate, session:models.SessionDep):
    db_user = models.User(
        name = user.name,
        email = user.email,
        hashed_password= user.password #need to be hashed later
    )

    if session.exec(select(models.User).where(models.User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    if db_user.id is None:
        raise HTTPException(status_code=500, detail="Failed to create user")

    
    return db_user

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