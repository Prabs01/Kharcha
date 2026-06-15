from fastapi import APIRouter
from app.models import Friendship

from app.services.friendship import create_friendship

import app.db as db

router = APIRouter(tags=["friends"])

@router.post('/users/{user_id}/friends/{friend_user_id}', response_model=Friendship)
def add_friend(user_id: int, friend_user_id: int, session: db.SessionDep):
   
    friendship = create_friendship(user_id, friend_user_id, session)
    return friendship
