from typing import Annotated
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query,Body, HTTPException

import models
from sqlmodel import select
from sqlalchemy.orm import selectinload

#lifecycle manager
#before yield - At startup
#after yield - At shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    models.create_db_and_table()
    yield

app = FastAPI(lifespan= lifespan)


@app.get('/')
async def home():
    return{"message": "welcome"}


@app.post(path='/users', response_model = models.UserRead)
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

@app.get('/users', response_model = list[models.UserRead])
async def read_users(
    session: models.SessionDep,
    offset: int = 0,
    limit: Annotated[int , Query(ge=1,le=100)] = 100,
):
    users = session.exec(select(models.User).offset(offset).limit(limit)).all()
    return users

@app.get(path="/users/{user_id}", response_model = models.UserRead)
async def read_user(user_id:int, session: models.SessionDep):
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete(path="/users/{user_id}")
async def delete_user(user_id:int, session:models.SessionDep):
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok" : True}


#-----Group operations -----

@app.post(path = "/groups", response_model=models.GroupRead)
async def create_group(group: models.GroupCreate, session: models.SessionDep):
    db_group = models.Group(name=group.name)
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    return db_group

@app.get(path = "/groups", response_model= list[models.GroupRead])
async def read_groups(
    session: models.SessionDep,
    offset: int = 0,
    limit: Annotated[int , Query(le=100)] = 100,
):
    groups = session.exec(select(models.Group).offset(offset).limit(limit)).all()
    return groups
    

@app.get(path = "/groups/{group_id}", response_model= models.GroupRead)
async def read_group(group_id: int, session:models.SessionDep):
    group = session.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@app.delete(path= '/groups/{group_id}')
async def delete_group(group_id: int, session:models.SessionDep):
    group = session.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    session.delete(group)

    session.commit()
    return {"ok": True}


@app.post(path = '/groups/{group_id}/members', response_model=models.GroupMemberRead)
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

@app.get(path = '/groups/{group_id}/members', response_model= list[models.UserRead])
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

@app.delete(path = '/groups/{group_id}/members/{user_id}')
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


#---- Expenses -----
@app.post(path = '/groups/{group_id}/expenses', response_model = models.ExpenseRead)
async def add_expense(
    group_id: int,
    expense: models.ExpenseCreate,
    session: models.SessionDep
):
    db_group = session.get(models.Group, group_id)
    if not db_group:
        raise HTTPException(status_code = 404, detail = "Group not found")

    db_user = session.get(models.User, expense.paid_by_user_id)
    if not db_user:
        raise HTTPException(status_code = 404, detail = "User not found")

    if not session.exec(
        select(models.GroupMember).where(models.GroupMember.group_id == group_id
            ).where(models.GroupMember.user_id == expense.paid_by_user_id)
        ).first():
        raise HTTPException(status_code = 400, detail = "User is not a member of the group")

    db_expense = models.Expenses(
        group_id = group_id,
        paid_by_user_id = expense.paid_by_user_id,
        title = expense.title,
        total_amount = expense.total_amount
    )  

    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)

    if not db_expense.id:
        raise HTTPException(status_code = 500, detail = "Failed to create expense") 

    output_expense = db_expense.to_read(db_user, db_group)

    return output_expense
    
@app.get(path = '/groups/{group_id}/expenses', response_model = list[models.ExpenseRead])
async def read_expenses_from_group(
    group_id: int,
    session: models.SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le = 100)] = 100
):
    db_group = session.get(models.Group, group_id)
    if not db_group:
        raise HTTPException(status_code = 404, detail = "Group not found")

    expenses = session.exec(
        select(models.Expenses)
        .options(selectinload(models.Expenses.paid_by_user)) #eager loading to avoid n+1 problem, it will load the paid_by_user relationship in the same query as the expenses, so we don't have to make a separate query for each expense to get the user.
        .where(models.Expenses.group_id == group_id)
        .offset(offset).limit(limit)
    ).all()

    output_expenses = []
    for expense in expenses:
        db_user = expense.paid_by_user
        output_expense = expense.to_read(db_user, db_group)
        output_expenses.append(output_expense)

    return output_expenses


@app.get(path = '/groups/{group_id}/expenses/{expense_id}', response_model=models.ExpenseRead)
async def read_expense(
    group_id: int,
    expense_id: int,
    session: models.SessionDep,
):
    db_group = session.get(models.Group, group_id)
    if not db_group:
        raise HTTPException(status_code = 404, detail = "Group not found")

    expense = session.get(models.Expenses, expense_id)
    if not expense:
        raise HTTPException(status_code = 404, detail = "Expense not found")

    if not expense.group_id == group_id:
        raise HTTPException(status_code = 404, detail = "Expense does not belong to the group")

    db_user = session.get(models.User, expense.paid_by_user_id)
    
    output_expense = expense.to_read(db_user, db_group)

    return output_expense

@app.delete(path = '/groups/{group_id}/expenses/{expense_id}')
async def delete_expense(
    group_id: int,
    expense_id: int,
    session: models.SessionDep,
):
    if not session.get(models.Group, group_id):
        raise HTTPException(status_code = 404, detail = "Group not found")

    expense = session.get(models.Expenses, expense_id)

    if not expense:
        raise HTTPException(status_code = 404, detail = "Expense not found")

    if not expense.group_id == group_id:
        raise HTTPException(status_code = 404, detail = "Expense does not belong to the group")

    session.delete(expense)
    session.commit()

    return {"ok": True}


@app.post(path = '/groups/{group_id}/expenses/{expense_id}/splits', response_model = models.ExpenseSplitsRead)
async def add_expense_split(
    group_id: int,
    expense_id: int,
    split: models.ExpenseSplitsCreate,
    session: models.SessionDep,
):
    if not session.get(models.Group, group_id):
        raise HTTPException(status_code = 404, detail = "Group not found")

    expense = session.get(models.Expenses, expense_id)

    if not expense:
        raise HTTPException(status_code = 404, detail = "Expense not found")

    if not expense.group_id == group_id:
        raise HTTPException(status_code = 404, detail = "Expense does not belong to the group")

    db_user = session.get(models.User, split.user_id)
    if not db_user:
        raise HTTPException(status_code = 404, detail = "User not found")

    db_split = models.ExpenseSplits(
        expense_id = expense_id,
        user_id = split.user_id,
        amount_owed = split.amount_owed,
        amount_paid = split.amount_paid
    )
    
    
    if not session.exec(select(models.GroupMember).where(models.GroupMember.group_id == group_id).where(models.GroupMember.user_id == split.user_id)).first():
        raise HTTPException(status_code = 404, detail = "User is not a member of the group")
    
    
    session.add(db_split)
    session.commit()
    session.refresh(db_split)

    if not db_split.id:
        raise HTTPException(status_code = 500, detail = "Failed to create expense split")

    output_split = db_split.to_read(db_user)

    return output_split


@app.get(path = '/groups/{group_id}/expenses/{expense_id}/splits', response_model = list[models.ExpenseSplitsRead])
async def read_expense_splits(
    group_id: int,
    expense_id: int,
    session: models.SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le = 100)] = 100
):
    if not session.get(models.Group, group_id):
        raise HTTPException(status_code = 404, detail = "Group not found")

    expense = session.get(models.Expenses, expense_id)
    if not expense:
        raise HTTPException(status_code = 404, detail = "Expense not found") 

    if not expense.group_id == group_id:
        raise HTTPException(status_code = 404, detail = "Expense doesnot belong to the group")

    splits = session.exec(
        select(models.ExpenseSplits)
        .options(selectinload(models.ExpenseSplits.user))
        .where(models.ExpenseSplits.expense_id == expense_id)
        .offset(offset).limit(limit)
    ).all()

    output_splits = []

    for split in splits:
        db_user = split.user
        db_split = split.to_read(db_user)
        output_splits.append(db_split)

    return output_splits
    