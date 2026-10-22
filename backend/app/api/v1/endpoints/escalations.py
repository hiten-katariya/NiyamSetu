from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, verify_csrf_token
from backend.app.core.exceptions import ForbiddenError, NotFoundError
from backend.app.db.session import get_db
from backend.app.models.entities import Application, Escalation, Institution, User
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from backend.app.schemas.escalations import EscalationResponse, ResolveEscalationRequest
from backend.app.services.escalation_service import EscalationService

router = APIRouter()


def serialize_escalation(esc: Escalation) -> EscalationResponse:
    app_no = esc.application.reference_no if esc.application else None
    inst_name = esc.application.institution.name if esc.application and esc.application.institution else None
    assigned_name = esc.assigned_to_user.full_name if esc.assigned_to_user else None

    return EscalationResponse(
        id=esc.id,
        application_id=esc.application_id,
        target_type=esc.target_type,
        target_id=esc.target_id,
        level=esc.level,
        assigned_to_user_id=esc.assigned_to_user_id,
        assigned_to_name=assigned_name,
        status=esc.status,
        triggered_at=esc.triggered_at,
        resolved_at=esc.resolved_at,
        resolution_notes=esc.resolution_notes,
        application_number=app_no,
        institution_name=inst_name,
    )


@router.get("", response_model=PaginatedResponse[EscalationResponse], summary="List Escalations")
def list_escalations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: open, resolved"),
    level: Optional[int] = Query(None, description="Filter by escalation level: 1, 2, 3"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns paginated escalations scoped to the user's administrative jurisdiction.
    """
    role_enum = normalize_role(current_user.role)

    stmt = (
        select(Escalation)
        .outerjoin(Escalation.application)
        .options(
            joinedload(Escalation.application).joinedload(Application.institution),
            joinedload(Escalation.assigned_to_user),
        )
    )

    if role_enum == UserRole.INSTITUTION_USER:
        if not current_user.institution_id:
            return {"data": [], "meta": PaginationMeta(page=page, page_size=limit, total=0, total_pages=1)}
        stmt = stmt.where(Application.institution_id == current_user.institution_id)

    elif role_enum == UserRole.REGIONAL_OFFICER:
        if not current_user.region_id:
            return {"data": [], "meta": PaginationMeta(page=page, page_size=limit, total=0, total_pages=1)}
        stmt = stmt.join(Application.institution).where(Institution.region_id == current_user.region_id)

    # Filter conditions
    if status_filter:
        stmt = stmt.where(Escalation.status == status_filter)
    if level is not None:
        stmt = stmt.where(Escalation.level == level)

    total_items = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    total_pages = max(1, (total_items + limit - 1) // limit)
    offset = (page - 1) * limit

    escalations = list(
        db.scalars(
            stmt.order_by(Escalation.triggered_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )

    return {
        "data": [serialize_escalation(e) for e in escalations],
        "meta": PaginationMeta(
            page=page,
            page_size=limit,
            total=total_items,
            total_pages=total_pages,
        ),
    }


@router.post("/{escalation_id}/resolve", response_model=DataResponse[EscalationResponse], summary="Resolve Escalation")
def resolve_escalation(
    escalation_id: uuid.UUID,
    payload: ResolveEscalationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Resolves an active escalation with mandatory review notes.
    Authorized for administrative and regional supervisory officers.
    """
    resolved_esc = EscalationService.resolve_escalation(
        db=db,
        escalation_id=escalation_id,
        user=current_user,
        resolution_notes=payload.resolution_notes,
    )
    # Refresh relations
    db.refresh(resolved_esc)
    return {"data": serialize_escalation(resolved_esc)}
