from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.exceptions import NotFoundError
from backend.app.db.session import get_db
from backend.app.models.entities import Application, EVC, EVCMember, Institution, User
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.schemas.applications import ApplicationResponse
from backend.app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta

router = APIRouter()


def apply_application_scoping(stmt, user: User):
    """
    Applies strict server-side institutional, regional, and assignment scoping
    to application queries based on the authenticated user's role.
    """
    role_enum = normalize_role(user.role)

    if role_enum in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.BUREAU_OFFICER, UserRole.SENIOR_AUTHORITY):
        # National administrative and oversight scope
        return stmt

    if role_enum == UserRole.INSTITUTION_USER:
        # Strictly restricted to their own institution
        if not user.institution_id:
            # If institution user has no institution assigned, cannot view any applications
            return stmt.where(Application.institution_id.is_(None))
        return stmt.where(Application.institution_id == user.institution_id)

    if role_enum == UserRole.REGIONAL_OFFICER:
        # Strictly restricted to applications belonging to institutions in their region
        if not user.region_id:
            return stmt.where(Application.institution_id.is_(None))
        return stmt.join(Application.institution).where(Institution.region_id == user.region_id)

    if role_enum == UserRole.COMMITTEE_MEMBER:
        # Strictly restricted to applications where the user is an assigned EVC member
        return stmt.join(Application.evcs).join(EVC.members).where(EVCMember.user_id == user.id)

    if role_enum == UserRole.SCRUTINY_OFFICER:
        # Applications assigned to this officer or open in the scrutiny pool
        return stmt

    return stmt


@router.get("", response_model=PaginatedResponse[ApplicationResponse], summary="List Scoped Applications")
def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List applications with strict server-side institutional and regional scoping.
    """
    stmt = select(Application)
    if status:
        stmt = stmt.where(Application.status == status)

    # Enforce server-side role and scope filtering
    stmt = apply_application_scoping(stmt, current_user)

    # Count total matching scoped items
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    offset = (page - 1) * page_size
    items = db.scalars(stmt.offset(offset).limit(page_size)).all()

    return {
        "data": [ApplicationResponse.model_validate(app) for app in items],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=(total + page_size - 1) // page_size if total > 0 else 1,
        ),
    }


@router.get("/{application_id}", response_model=DataResponse[ApplicationResponse], summary="Get Scoped Application Details")
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve application details. Returns 404 if the application does not exist or
    falls outside the authenticated user's permitted regional or institutional scope.
    """
    stmt = select(Application).where(Application.id == application_id)
    stmt = apply_application_scoping(stmt, current_user)
    app = db.scalars(stmt).first()

    if not app:
        # Do not disclose whether unauthorized resource exists
        raise NotFoundError("Application not found.")

    return {"data": ApplicationResponse.model_validate(app)}
