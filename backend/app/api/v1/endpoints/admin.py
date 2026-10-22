from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles, verify_csrf_token
from backend.app.db.session import get_db
from backend.app.models.entities import (
    ConfigVersion,
    EscalationRule,
    Holiday,
    MessageTemplate,
    ReminderRule,
    RouteStage,
    RouteType,
    User,
)
from backend.app.permissions.roles import UserRole
from backend.app.schemas.admin import (
    ConfigVersionSchema,
    EscalationRuleCreateUpdateRequest,
    EscalationRuleSchema,
    HolidayCreateRequest,
    HolidaySchema,
    MessageTemplateSchema,
    MessageTemplateUpdateRequest,
    ReminderRuleCreateUpdateRequest,
    ReminderRuleSchema,
    RouteStageSchema,
    RouteTypeSchema,
    StageUpdateRequest,
)
from backend.app.schemas.auth import AccountStatusUpdateRequest, RoleUpdateRequest, UserResponse
from backend.app.schemas.common import DataResponse
from backend.app.services.auth_service import AuthService
from backend.app.services.config_service import ConfigService

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


# ==========================================
# Workflow Route Types & Stages Configuration
# ==========================================

@router.get("/route-types", response_model=DataResponse[List[RouteTypeSchema]], summary="List Route Types")
def list_route_types(db: Session = Depends(get_db)):
    """
    Returns configured route types with ordered stage definitions.
    """
    stmt = select(RouteType).where(RouteType.is_active == True)
    routes = db.scalars(stmt).all()
    return {"data": routes}


@router.patch(
    "/stages/{stage_id}",
    response_model=DataResponse[RouteStageSchema],
    summary="Update Stage Timeline & Configuration",
    dependencies=[Depends(verify_csrf_token)],
)
def update_stage(
    stage_id: uuid.UUID,
    payload: StageUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    """
    Updates workflow stage parameters with mandatory change reason and version tracking.
    Preserves historical route version pinning for in-flight applications.
    """
    client_ip = request.client.host if request.client else None
    stage = ConfigService.update_route_stage(
        db=db,
        stage_id=stage_id,
        stage_name=payload.stage_name,
        timeline_days=payload.timeline_days,
        day_type=payload.day_type,
        required_role=payload.required_role,
        is_required=payload.is_required,
        change_reason=payload.change_reason,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": stage}


# ==========================================
# Reminder Rules Configuration
# ==========================================

@router.get("/rules/reminders", response_model=DataResponse[List[ReminderRuleSchema]], summary="List Reminder Rules")
def list_reminder_rules(db: Session = Depends(get_db)):
    """
    Returns configurable reminder rules and offsets.
    """
    stmt = select(ReminderRule).order_by(ReminderRule.days_before_due.asc())
    rules = db.scalars(stmt).all()
    return {"data": rules}


@router.post(
    "/rules/reminders",
    response_model=DataResponse[ReminderRuleSchema],
    summary="Create Reminder Rule",
    dependencies=[Depends(verify_csrf_token)],
)
def create_reminder_rule(
    payload: ReminderRuleCreateUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request.client else None
    rule = ConfigService.create_reminder_rule(
        db=db,
        name=payload.name,
        target_type=payload.target_type,
        days_before_due=payload.days_before_due,
        recipient_roles=payload.recipient_roles,
        is_active=payload.is_active,
        change_reason=payload.change_reason,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": rule}


@router.put(
    "/rules/reminders/{rule_id}",
    response_model=DataResponse[ReminderRuleSchema],
    summary="Update Reminder Rule",
    dependencies=[Depends(verify_csrf_token)],
)
def update_reminder_rule(
    rule_id: uuid.UUID,
    payload: ReminderRuleCreateUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request.client else None
    rule = ConfigService.update_reminder_rule(
        db=db,
        rule_id=rule_id,
        name=payload.name,
        target_type=payload.target_type,
        days_before_due=payload.days_before_due,
        recipient_roles=payload.recipient_roles,
        is_active=payload.is_active,
        change_reason=payload.change_reason,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": rule}


@router.delete(
    "/rules/reminders/{rule_id}",
    summary="Delete Reminder Rule",
    dependencies=[Depends(verify_csrf_token)],
)
def delete_reminder_rule(
    rule_id: uuid.UUID,
    change_reason: str = Query(..., min_length=3),
    request: Request = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request and request.client else None
    ConfigService.delete_reminder_rule(
        db=db,
        rule_id=rule_id,
        change_reason=change_reason,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": {"message": "Reminder rule deleted successfully"}}


# ==========================================
# Escalation Rules Configuration
# ==========================================

@router.get("/rules/escalations", response_model=DataResponse[List[EscalationRuleSchema]], summary="List Escalation Rules")
def list_escalation_rules(db: Session = Depends(get_db)):
    """
    Returns configurable escalation level rules.
    """
    stmt = select(EscalationRule).order_by(EscalationRule.level.asc(), EscalationRule.days_after_due.asc())
    rules = db.scalars(stmt).all()
    return {"data": rules}


@router.post(
    "/rules/escalations",
    response_model=DataResponse[EscalationRuleSchema],
    summary="Create Escalation Rule",
    dependencies=[Depends(verify_csrf_token)],
)
def create_escalation_rule(
    payload: EscalationRuleCreateUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request.client else None
    rule = ConfigService.create_escalation_rule(
        db=db,
        name=payload.name,
        target_type=payload.target_type,
        level=payload.level,
        days_after_due=payload.days_after_due,
        recipient_roles=payload.recipient_roles,
        is_active=payload.is_active,
        change_reason=payload.change_reason,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": rule}


@router.put(
    "/rules/escalations/{rule_id}",
    response_model=DataResponse[EscalationRuleSchema],
    summary="Update Escalation Rule",
    dependencies=[Depends(verify_csrf_token)],
)
def update_escalation_rule(
    rule_id: uuid.UUID,
    payload: EscalationRuleCreateUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request.client else None
    rule = ConfigService.update_escalation_rule(
        db=db,
        rule_id=rule_id,
        name=payload.name,
        target_type=payload.target_type,
        level=payload.level,
        days_after_due=payload.days_after_due,
        recipient_roles=payload.recipient_roles,
        is_active=payload.is_active,
        change_reason=payload.change_reason,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": rule}


@router.delete(
    "/rules/escalations/{rule_id}",
    summary="Delete Escalation Rule",
    dependencies=[Depends(verify_csrf_token)],
)
def delete_escalation_rule(
    rule_id: uuid.UUID,
    change_reason: str = Query(..., min_length=3),
    request: Request = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request and request.client else None
    ConfigService.delete_escalation_rule(
        db=db,
        rule_id=rule_id,
        change_reason=change_reason,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": {"message": "Escalation rule deleted successfully"}}


# ==========================================
# Holiday Calendars Configuration
# ==========================================

@router.get("/holidays", response_model=DataResponse[List[HolidaySchema]], summary="List Configured Holidays")
def list_holidays(
    region_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(Holiday).order_by(Holiday.holiday_date.asc())
    if region_id:
        stmt = stmt.where(Holiday.region_id.in_([region_id, None]))
    holidays = db.scalars(stmt).all()
    return {"data": holidays}


@router.post(
    "/holidays",
    response_model=DataResponse[HolidaySchema],
    summary="Add Holiday to Calendar",
    dependencies=[Depends(verify_csrf_token)],
)
def create_holiday(
    payload: HolidayCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request.client else None
    hol = ConfigService.create_holiday(
        db=db,
        name=payload.name,
        holiday_date=payload.holiday_date,
        region_id=payload.region_id,
        change_reason=payload.change_reason,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": hol}


@router.delete(
    "/holidays/{holiday_id}",
    summary="Delete Holiday",
    dependencies=[Depends(verify_csrf_token)],
)
def delete_holiday(
    holiday_id: uuid.UUID,
    change_reason: str = Query(..., min_length=3),
    request: Request = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request and request.client else None
    ConfigService.delete_holiday(
        db=db,
        holiday_id=holiday_id,
        change_reason=change_reason,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": {"message": "Holiday deleted successfully"}}


# ==========================================
# Message Templates Configuration
# ==========================================

@router.get("/message-templates", response_model=DataResponse[List[MessageTemplateSchema]], summary="List Message Templates")
def list_message_templates(db: Session = Depends(get_db)):
    stmt = select(MessageTemplate).order_by(MessageTemplate.code.asc())
    tpls = db.scalars(stmt).all()
    return {"data": tpls}


@router.put(
    "/message-templates/{template_id}",
    response_model=DataResponse[MessageTemplateSchema],
    summary="Update Message Template",
    dependencies=[Depends(verify_csrf_token)],
)
def update_message_template(
    template_id: uuid.UUID,
    payload: MessageTemplateUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request.client else None
    tpl = ConfigService.update_message_template(
        db=db,
        template_id=template_id,
        subject_template=payload.subject_template,
        body_template=payload.body_template,
        is_active=payload.is_active,
        change_reason=payload.change_reason,
        actor_user=admin_user,
        ip_address=client_ip,
    )
    return {"data": tpl}


# ==========================================
# Configuration Version History
# ==========================================

@router.get("/config/versions", response_model=DataResponse[List[ConfigVersionSchema]], summary="Configuration Version History")
def list_config_versions(
    config_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Returns chronological audit history of all system configuration changes with mandatory reasons.
    """
    stmt = select(ConfigVersion).order_by(ConfigVersion.created_at.desc()).limit(limit)
    if config_type:
        stmt = stmt.where(ConfigVersion.config_type == config_type)
    versions = db.scalars(stmt).all()
    return {"data": versions}
