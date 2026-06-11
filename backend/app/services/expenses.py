from typing import List
from app.models import Expenses, ExpenseSplits
from app.schemas import SplitMethod, SplitPartipant

from fastapi import HTTPException
from app.models import SessionDep


def split_expense(expense: Expenses, split_method:SplitMethod, split_participants: List[SplitPartipant] | None, session:SessionDep):

    if split_method == SplitMethod.EQUAL:
        split_expense_equally(expense, session)
    elif split_method == SplitMethod.EXACT:
        split_expense_exact(expense, split_participants, session)
    elif split_method == SplitMethod.PERCENTAGE:
        split_expense_percentage(expense, split_participants, session)

def split_expense_equally(expense: Expenses, session:SessionDep):

    total_amount = expense.total_amount

    users = expense.group.members

    split_amount = total_amount / len(users)

    for user in users:

        if user is expense.paid_by_user:

            assert user.id is not None
            assert expense.id is not None

            split = ExpenseSplits(
                expense_id = expense.id,
                user_id = user.id,
                amount_owed = split_amount,
                amount_paid = total_amount
            )
            session.add(split)

            if not split.id:
                session.flush()  # Ensure the split ID is generated
            print(f"Split added: {split}")

        else:
            
            assert user.id is not None
            assert expense.id is not None

            split = ExpenseSplits(
                expense_id = expense.id,
                user_id = user.id,
                amount_owed = split_amount,
                amount_paid = 0
            )
            session.add(split)

            if not split.id:
                session.flush()  # Ensure the split ID is generated
            print(f"Split added: {split}")

    session.commit()
    


def split_expense_exact(expense: Expenses, split_participants: List[SplitPartipant] | None, session:SessionDep):

    total_amount = expense.total_amount

    splits = split_participants

    if not splits:
        raise HTTPException(status_code=422, detail="Splits must be provided for exact split method")

    total_split_amount = sum(split.amount for split in splits)

    if total_amount != total_split_amount:
        raise HTTPException(status_code=422, detail="Total split amount does not match the total expense amount")

    for split in splits:

        assert split.user_id is not None
        assert expense.id is not None
        assert split.amount is not None

        db_split = ExpenseSplits(
            expense_id = expense.id,
            user_id = split.user_id,
            amount_owed = split.amount,
            amount_paid = total_split_amount if split.user_id == expense.paid_by_user_id else 0
        )
        session.add(db_split)
        if not db_split.id:
            session.flush()  # Ensure the split ID is generated

    session.commit()

def split_expense_percentage(expense: Expenses, split_participants: List[SplitPartipant] | None, session:SessionDep):
    
    total_amount = expense.total_amount

    splits = split_participants

    if not splits:
        raise HTTPException(status_code=422, detail="Splits must be provided for percentage split method")

    total_split_percentage = sum(split.percentage for split in splits)

    if total_split_percentage != 100:
        raise HTTPException(status_code=422, detail="Total split percentage must be 100")

    for split in splits:

        assert split.user_id is not None
        assert expense.id is not None
        assert split.percentage is not None

        split_amount = (split.percentage / 100) * total_amount

        db_split = ExpenseSplits(
            expense_id = expense.id,
            user_id = split.user_id,
            amount_owed = split_amount,
            amount_paid = total_amount if split.user_id == expense.paid_by_user_id else 0
        )
        session.add(db_split)
        if not db_split.id:
            session.flush()  # Ensure the split ID is generated
    session.commit()