from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles, verify_csrf_token
from backend.app.db.session import get_db
from backend.app.models.entities import EscalationRule, ReminderRule, RouteType, User
from backend.app.permissions.roles import UserRole
from backend.app.schemas.admin import EscalationRuleSchema, ReminderRuleSchema, RouteTypeSchema
from backend.app.schemas.auth import AccountStatusUpdateRequest, RoleUpdateRequest, UserResponse
from backend.app.schemas.common import DataResponse
from backend.app.services.auth_service import AuthService

router = APIRouter(dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.SYSTEM_ADMIN))])


@router.get("/users", response_model=DataResponse[List[UserResponse]], summary="List System Users (Admin only)")
def list_users(db: Session = Depends(get_db)):
    """
    Returns all registered users in the system. Restricted to administrators.
    """
    stmt = select(User).order_by(User.created_at.asc())
    users = db.scalars(stmt).all()
    return {"data": [UserResponse.model_validate(u) for u in users]}


@router.patch(
    "/users/{user_id}/role",
    response_model=DataResponse[UserResponse],
    summary="Update User Role & Assignment Scope (Admin only)",
    dependencies=[Depends(verify_csrf_token)],
)
def update_user_role(
    user_id: uuid.UUID,
    payload: RoleUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    """
    Updates a user's role and scopes with validation and audit logging.
    Revokes the target user's existing sessions so new permissions take effect.
    """
    client_ip = request.client.host if request.client else None
    updated = AuthService.update_user_role(
        db=db,
        target_user_id=user_id,
        new_role=payload.role,
        actor_user=admin_user,
        region_id=payload.region_id,
        institution_id=payload.institution_id,
        ip_address=client_ip,
    )
    return {"data": UserResponse.model_validate(updated)}


@router.patch(
    "/users/{user_id}/status",
    response_model=DataResponse[UserResponse],
    summary="Activate / Deactivate User Account (Admin only)",
    dependencies=[Depends(verify_csrf_token)],
)
def update_account_status(
    user_id: uuid.UUID,
    payload: AccountStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    """
    Activates or deactivates an account. Deactivation immediately invalidates all active sessions.
    """
    client_ip = request.client.host if request.client else None
    updated = AuthService.update_account_status(
        db=db,
        target_user_id=user_id,
        is_active=payload.is_active,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": UserResponse.model_validate(updated)}


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
