import app.models as models
import app.schemas as schemas
import app.db as db

from fastapi import HTTPException

from sqlmodel import select



def calculate_balance(group_id: int, session:db.SessionDep):

    group = session.get(models.Group, group_id)

    if not group:
        raise HTTPException(status_code= 404, detail = "Group not found")

    expenses = group.expenses
    member_ids = [x.id for x in group.members]

    balances = {member_id:0.0 for member_id in member_ids if member_id is not None}

    for expense in expenses:
        for split in expense.splits:
            if split.user_id in member_ids:
                balances[split.user_id] += split.amount_paid
                balances[split.user_id] -= split.amount_owed

    settlements = group.settlements
    for settlement in settlements:
        if settlement.status == schemas.SettlementStatus.COMPLETED:
            if settlement.from_user_id in member_ids:
                balances[settlement.from_user_id] += settlement.amount
            if settlement.to_user_id in member_ids:
                balances[settlement.to_user_id] -= settlement.amount

    return [{
        "user_id": user_id,
        "balance": balance
    } for user_id, balance in balances.items()
    ]


def calculate_settlement(group_id: int, session:db.SessionDep):

    balances = calculate_balance(group_id, session)

    # Separate users into creditors and debtors
    creditors = [b for b in balances if b["balance"] > 0]
    debtors = [b for b in balances if b["balance"] < 0]

    settlements = []

    # Simple greedy algorithm to settle debts
    for debtor in debtors:
        amount_to_settle = -debtor["balance"]
        for creditor in creditors:
            if amount_to_settle <= 0:
                break
            amount_from_creditor = min(creditor["balance"], amount_to_settle)
            settlements.append({
                "from_user_id": debtor["user_id"],
                "to_user_id": creditor["user_id"],
                "amount": amount_from_creditor
            })
            creditor["balance"] -= amount_from_creditor
            amount_to_settle -= amount_from_creditor

    return settlements

def create_settlement(group_id: int, payload: models.SettlementCreate, session: db.SessionDep):

    if not session.get(models.Group, group_id):
        raise HTTPException(status_code= 404, detail = "Group not found")

    from_user = session.get(models.User, payload.from_user_id)
    to_user = session.get(models.User, payload.to_user_id)

    if not from_user:
        raise HTTPException(status_code= 404, detail = "From user not found")

    if not to_user:
        raise HTTPException(status_code= 404, detail = "To user not found")

    if not session.exec(select(models.GroupMember).where(models.GroupMember.group_id == group_id).where(models.GroupMember.user_id == payload.from_user_id)).first():
        raise HTTPException(status_code= 404, detail = "From user is not a member of the group")

    if not session.exec(select(models.GroupMember).where(models.GroupMember.group_id == group_id).where(models.GroupMember.user_id == payload.to_user_id)).first():
        raise HTTPException(status_code= 404, detail = "To user is not a member of the group")
    

    settlement =models.Settlement(
        group_id=group_id,
        from_user_id=payload.from_user_id,
        to_user_id=payload.to_user_id,
        amount=payload.amount
    )

    session.add(settlement)
    session.commit()
    session.refresh(settlement)

    return settlement