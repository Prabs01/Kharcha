from sqlmodel import select
from fastapi import APIRouter
import app.models as models
import app.db as db
from fastapi import HTTPException

import app.services.analytics as analytics_service

router = APIRouter(tags=["analytics"])

@router.get('/groups/{group_id}/balances')
async def get_group_balances(group_id: int, session: db.SessionDep):
    
    balances = analytics_service.calculate_balance(group_id, session)

    return {"group_id": group_id, "balances": balances}


@router.post('/groups/{group_id}/settlements')
async def create_group_settlement(group_id: int, payload: models.SettlementCreate, session: db.SessionDep):
    
    settlement = analytics_service.create_settlement(group_id, payload, session)

    return settlement

@router.get('/groups/{group_id}/settlements')
async def get_group_settlements(group_id: int, session: db.SessionDep):
    
    if not session.get(models.Group, group_id):
        raise HTTPException(status_code= 404, detail = "Group not found")

    settlements = session.exec(
        select(models.Settlement).where(models.Settlement.group_id == group_id)
    ).all()

    return {"group_id": group_id, "settlements": settlements}

@router.get('/groups/{group_id}/settlements/suggested')
async def get_suggested_settlements(group_id: int, session: db.SessionDep):
    
    settlements = analytics_service.calculate_settlement(group_id, session)

    return {"group_id": group_id, "settlements": settlements}


