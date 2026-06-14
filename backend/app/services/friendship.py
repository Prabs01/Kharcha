
import app.db as db
import app.models as models
from sqlmodel import select
from fastapi import HTTPException

def create_friendship(user_id: int, friend_user_id: int, session: db.SessionDep):
    # Check if both users exist
    user = session.get(models.User, user_id)
    friend_user = session.get(models.User, friend_user_id)

    if not user or not friend_user:
        raise HTTPException(status_code=404, detail="One or both users not found")

    if friend_user_id in [friend.friend_user_id for friend in user.friendships] or user_id in [friend.friend_user_id for friend in friend_user.friendships]:
        raise HTTPException(status_code=400, detail="Friendship already exists")

    # Create the friendship
    friendship = models.Friendship(user_id=user_id, friend_user_id=friend_user_id)
    session.add(friendship)
    session.commit()
    session.refresh(friendship)

    return friendship