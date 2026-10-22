from datetime import date, datetime
from typing import Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.entities import Application, AuditLog, Institution, User
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.schemas.audit import AuditLogEntrySchema, AuditVerificationResponse
from backend.app.schemas.common import DataResponse, PaginatedResponse
from backend.app.services.audit_service import AuditService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/logs", summary="Search Audit Log Trail")
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    actor_user_id: Optional[uuid.UUID] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns permission-scoped, paginated immutable audit logs.
    """
    role_enum = normalize_role(current_user.role)
    stmt = select(AuditLog)

    # Scoping
    if role_enum == UserRole.INSTITUTION_USER:
        # Only actions taken by this user or relating to their institution applications
        inst_app_ids = [
            str(a_id)
            for a_id in db.scalars(
                select(Application.id).where(Application.institution_id == current_user.institution_id)
            ).all()
        ]
        stmt = stmt.where(
            (AuditLog.actor_user_id == current_user.id)
            | (AuditLog.entity_id.in_(inst_app_ids))
        )
    elif role_enum == UserRole.REGIONAL_OFFICER:
        if current_user.region_id:
            reg_app_ids = [
                str(a_id)
                for a_id in db.scalars(
                    select(Application.id)
                    .join(Application.institution)
                    .where(Institution.region_id == current_user.region_id)
                ).all()
            ]
            stmt = stmt.where(
                (AuditLog.actor_user_id == current_user.id)
                | (AuditLog.entity_id.in_(reg_app_ids))
            )

    # Optional Filters
    if actor_user_id:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if start_date:
        stmt = stmt.where(func.date(AuditLog.occurred_at) >= start_date)
    if end_date:
        stmt = stmt.where(func.date(AuditLog.occurred_at) <= end_date)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    entries = list(
        db.scalars(
            stmt.order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )

    # Map actor names
    actor_ids = [e.actor_user_id for e in entries if e.actor_user_id]
    actor_map: Dict[uuid.UUID, str] = {}
    if actor_ids:
        users = db.scalars(select(User).where(User.id.in_(actor_ids))).all()
        actor_map = {u.id: u.full_name for u in users}

    items = []
    for e in entries:
        items.append(
            AuditLogEntrySchema(
                id=e.id,
                actor_user_id=e.actor_user_id,
                actor_name=actor_map.get(e.actor_user_id, "System Automated" if not e.actor_user_id else "User"),
                action=e.action,
                entity_type=e.entity_type,
                entity_id=e.entity_id,
                occurred_at=e.occurred_at,
                ip_address=e.ip_address,
                metadata_=e.metadata_,
                entry_hash=e.entry_hash,
            )
        )

    return {
        "data": items,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }


@router.get(
    "/verify-integrity",
    response_model=DataResponse[AuditVerificationResponse],
    summary="Verify Cryptographic Audit Hash Chain",
)
def verify_audit_integrity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validates the SHA-256 cryptographic hash chain of all audit entries.
    Confirms zero tampering, omissions, or out-of-order mutations.
    """
    is_valid, err_msg, count = AuditService.verify_chain(db)
    return {
        "data": AuditVerificationResponse(
            is_valid=is_valid,
            verified_count=count,
            error_message=err_msg,
        )
    }
