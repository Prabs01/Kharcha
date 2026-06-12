from fastapi import APIRouter, HTTPException, Query
import app.models as models
import app.db as db
import app.schemas as schemas
from sqlmodel import select
from typing import Annotated
from sqlalchemy.orm import selectinload
import app.services.expenses as expense_services

import logging
logger = logging.getLogger(__name__)


router = APIRouter(tags=["expenses"])


#---- Expenses -----
@router.post(path = '/groups/{group_id}/expenses', response_model = schemas.ExpenseRead)
async def add_expense(
    group_id: int,
    expense: schemas.ExpenseCreate,
    session: db.SessionDep
):
    db_group = session.get(models.Group, group_id)
    if not db_group:
        raise HTTPException(status_code = 404, detail = "Group not found")
    logger.info("Adding expense to group %d: %s", group_id, expense)

    db_user = session.get(models.User, expense.paid_by_user_id)
    if not db_user:
        raise HTTPException(status_code = 404, detail = "User not found")
    logger.info("Expense paid by user %d: %s", expense.paid_by_user_id, db_user)

    if not session.exec(
        select(models.GroupMember).where(models.GroupMember.group_id == group_id
            ).where(models.GroupMember.user_id == expense.paid_by_user_id)
        ).first():
        raise HTTPException(status_code = 400, detail = "User is not a member of the group")
    logger.info("User %d is a member of group %d", expense.paid_by_user_id, group_id)

    db_expense = models.Expenses(
        group_id = group_id,
        paid_by_user_id = expense.paid_by_user_id,
        title = expense.title,
        total_amount = expense.total_amount,
    )  

    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)

    if not db_expense.id:
        raise HTTPException(status_code = 500, detail = "Failed to create expense") 
    logger.info("Created expense with id %d", db_expense.id)

    output_expense = db_expense.to_read(db_user, db_group)
    expense_services.split_expense(db_expense, expense.split_method, expense.split_participants, session)

    return output_expense
    
@router.get(path = '/groups/{group_id}/expenses', response_model = list[schemas.ExpenseRead])
async def read_expenses_from_group(
    group_id: int,
    session: db.SessionDep,
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


@router.get(path = '/groups/{group_id}/expenses/{expense_id}', response_model=schemas.ExpenseRead)
async def read_expense(
    group_id: int,
    expense_id: int,
    session: db.SessionDep,
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

@router.delete(path = '/groups/{group_id}/expenses/{expense_id}')
async def delete_expense(
    group_id: int,
    expense_id: int,
    session: db.SessionDep,
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


@router.post(path = '/groups/{group_id}/expenses/{expense_id}/splits', response_model = models.ExpenseSplitsRead)
async def add_expense_split(
    group_id: int,
    expense_id: int,
    split: schemas.ExpenseSplitsCreate,
    session: db.SessionDep,
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


@router.get(path = '/groups/{group_id}/expenses/{expense_id}/splits', response_model = list[models.ExpenseSplitsRead])
async def read_expense_splits(
    group_id: int,
    expense_id: int,
    session: db.SessionDep,
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
    