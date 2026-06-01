from fastapi import APIRouter, HTTPException, Query, Body

import app.models as models
from sqlmodel import select
from typing import Annotated

router = APIRouter(tags=["groups"])


#-----Group operations -----

@router.post(path = "/groups", response_model=models.GroupRead)
async def create_group(group: models.GroupCreate, session: models.SessionDep):
    db_group = models.Group(name=group.name)
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    return db_group

@router.get(path = "/groups", response_model= list[models.GroupRead])
async def read_groups(
    session: models.SessionDep,
    offset: int = 0,
    limit: Annotated[int , Query(le=100)] = 100,
):
    groups = session.exec(select(models.Group).offset(offset).limit(limit)).all()
    return groups
    

@router.get(path = "/groups/{group_id}", response_model= models.GroupRead)
async def read_group(group_id: int, session:models.SessionDep):
    group = session.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.delete(path= '/groups/{group_id}')
async def delete_group(group_id: int, session:models.SessionDep):
    group = session.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    session.delete(group)

    session.commit()
    return {"ok": True}


@router.post(path = '/groups/{group_id}/members', response_model=models.GroupMemberRead)
async def add_member_to_group(
    group_id: int,
    session: models.SessionDep,
    user: models.GroupMemberCreate = Body(),
):
    group = session.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if not session.get(models.User, user.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    group_member = models.GroupMember(group_id= group_id, user_id = user.user_id)

    if session.exec(select(models.GroupMember).where(models.GroupMember.group_id == group_id).where(models.GroupMember.user_id == user.user_id)).first():
        raise HTTPException(status_code=400, detail="User is already a member of the group")

    session.add(group_member)
    session.commit()
    session.refresh(group_member)

    db_user = group_member.user

    if group_member.id is None:
        raise HTTPException(status_code=500, detail="Failed to create group member")

    return group_member.to_read(db_user)

@router.get(path = '/groups/{group_id}/members', response_model= list[models.UserRead])
async def read_members_from_group(
    group_id: int,
    session: models.SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    
    db_group = session.get(models.Group, group_id)

    if not db_group:
        raise HTTPException(status_code = 404, detail="Group not found")

    statement = (
    select(models.User)
    .join(models.GroupMember)
    .where(models.GroupMember.group_id == group_id)
    .offset(offset)
    .limit(limit)
)
    members = session.exec(statement).all()


    output_members = [member.to_read() for member in members]
    
    return output_members

@router.delete(path = '/groups/{group_id}/members/{user_id}')
async def delete_member_from_group(
    group_id: int,
    user_id: int,
    session: models.SessionDep,
):
    if not session.get(models.Group, group_id):
        raise HTTPException(status_code = 404, detail="Group not found")

    member = session.exec(
        select(models.GroupMember).where(models.GroupMember.group_id == group_id).where(models.GroupMember.user_id == user_id)
    ).first()
    if not member:
        raise HTTPException(status_code = 404, detail="Member not found")
    session.delete(member)
    session.commit()
    return {"ok":True}

