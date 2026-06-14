from fastapi import APIRouter

router = APIRouter(tags=["friends"])

@router.post('/users/{user_id}/friends/{friend_user_id}')
def add_friend(user_id: int, friend_user_id: int):
    # Logic to add friend relationship between user_id and friend_user_id
    return {"message": f"User {user_id} and User {friend_user_id} are now friends."}