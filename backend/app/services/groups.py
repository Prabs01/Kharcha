from fastapi import HTTPException, Body
from app.models import SessionDep, Group, GroupMember, GroupMemberCreate, User
from app.auth import CurrentUser

from sqlmodel import select

def get_group(group_id: int, current_user: CurrentUser, session: SessionDep):

    group = session.get(Group, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members = group.members

    if current_user not in members:
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    return group

def delete_group(group_id: int, current_user: CurrentUser, session: SessionDep):
    group = session.get(Group, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members = group.members

    if current_user not in members:
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    session.delete(group)
    session.commit()
    return {"ok": True}

def get_groups_for_user(current_user: CurrentUser, session: SessionDep):

    groups = session.exec(
        select(Group).join(GroupMember).where(GroupMember.user_id == current_user.id)
    ).all()

    if not groups:
        raise HTTPException(status_code=404, detail="No groups found for this user")

    return groups

def add_member_to_group(group_id: int, current_user: CurrentUser, session: SessionDep, user: GroupMemberCreate = Body()):

    group = session.get(Group, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members = group.members

    if user.user_id in [member.id for member in members]:
        raise HTTPException(status_code=400, detail="User is already a member of the group")

    if not session.get(User, user.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    if current_user not in members:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    
    group_member = GroupMember(group_id=group_id, user_id=user.user_id)
    session.add(group_member)
    session.commit()
    session.refresh(group_member)

    return group_member.to_read(group_member.user)

def get_members_from_group(group_id: int, current_user: CurrentUser, session: SessionDep, offset: int = 0, limit: int = 100):

    group = session.get(Group, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members = group.members
    if current_user not in members:
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    return [member.to_read() for member in members]

def remove_member_from_group(group_id: int, user_id: int, current_user: CurrentUser, session: SessionDep):

    group = session.get(Group, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members = group.members
    if current_user not in members:
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    member = session.exec(
        select(GroupMember).where(GroupMember.group_id == group_id).where(GroupMember.user_id == user_id)
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    session.delete(member)
    session.commit()
    return {"ok": True}