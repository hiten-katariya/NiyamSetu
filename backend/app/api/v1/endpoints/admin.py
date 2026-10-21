from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import EscalationRule, ReminderRule, RouteType
from backend.app.schemas.admin import EscalationRuleSchema, ReminderRuleSchema, RouteTypeSchema
from backend.app.schemas.common import DataResponse

router = APIRouter()


@router.get("/route-types", response_model=DataResponse[List[RouteTypeSchema]], summary="List Route Types")
def list_route_types(db: Session = Depends(get_db)):
    """
    Returns configured route types with ordered stage definitions.
    """
    stmt = select(RouteType).where(RouteType.is_active == True)
    routes = db.scalars(stmt).all()
    return {"data": routes}


@router.get("/rules/reminders", response_model=DataResponse[List[ReminderRuleSchema]], summary="List Reminder Rules")
def list_reminder_rules(db: Session = Depends(get_db)):
    """
    Returns configurable reminder rules and offsets.
    """
    stmt = select(ReminderRule).where(ReminderRule.is_active == True)
    rules = db.scalars(stmt).all()
    return {"data": rules}


@router.get("/rules/escalations", response_model=DataResponse[List[EscalationRuleSchema]], summary="List Escalation Rules")
def list_escalation_rules(db: Session = Depends(get_db)):
    """
    Returns configurable escalation level rules.
    """
    stmt = select(EscalationRule).where(EscalationRule.is_active == True)
    rules = db.scalars(stmt).all()
    return {"data": rules}
