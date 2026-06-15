import app.db as db
import app.models as models
from fastapi import HTTPException
from sqlmodel import select

def create_friendship(user_id: int, friend_user_id: int, session: db.SessionDep):
    
    if user_id == friend_user_id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as a friend")

    u1, u2 = sorted([user_id, friend_user_id])

    existing_friendship = session.exec(
        select(models.Friendship).where(
            models.Friendship.user_low_id == u1,
            models.Friendship.user_high_id == u2,
        )
    ).first()
    
    if existing_friendship:
        raise HTTPException(status_code=400, detail="Friendship already exists")

    friendship = models.Friendship(user_low_id=u1, user_high_id=u2)
    session.add(friendship)
    session.commit()
    session.refresh(friendship)

    return friendship