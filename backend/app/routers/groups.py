from fastapi import APIRouter, HTTPException, Depends

import app.models as models
import app.schemas as schemas
from typing import Annotated

from app.auth import CurrentUser

import app.services.groups as groups_service

router = APIRouter(tags=["groups"])


#-----Group operations -----

@router.post(path = "/groups", response_model=models.GroupRead)
async def create_group(
    group: schemas.GroupCreate,
    session: models.SessionDep,
    current_user: CurrentUser,
):
    db_group = models.Group(name=group.name)
    session.add(db_group)
    session.commit()
    session.refresh(db_group)

    if db_group.id is None or current_user.id is None:
        raise HTTPException(status_code=500, detail="Failed to create group")

    session.add(models.GroupMember(group_id=db_group.id, user_id=current_user.id))
    session.commit()

    return db_group

@router.get(path = "/groups", response_model= list[models.GroupRead])
async def read_groups(
    groups: Annotated[list[models.Group], Depends(groups_service.get_groups_for_user)],
):
    return groups
    

@router.get(path = "/groups/{group_id}", response_model= models.GroupRead)
async def read_group(group: Annotated[models.Group, Depends(groups_service.get_group)]):
    return group


@router.delete(path= '/groups/{group_id}')
async def delete_group(delete_group_response: Annotated[dict, Depends(groups_service.delete_group)]):
    return delete_group_response

@router.post(path = '/groups/{group_id}/members', response_model=models.GroupMemberRead)
async def add_member_to_group(
    group_member: Annotated[models.GroupMemberRead, Depends(groups_service.add_member_to_group)],
):
    return group_member

@router.get(path = '/groups/{group_id}/members', response_model= list[models.UserRead])
async def read_members_from_group(
    members: Annotated[list[models.User], Depends(groups_service.get_members_from_group)],
):
    return members

@router.delete(path = '/groups/{group_id}/members/{user_id}')
async def delete_member_from_group(
    delete_member_response: Annotated[dict, Depends(groups_service.remove_member_from_group)],
):
    return delete_member_response

