from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, verify_csrf_token
from backend.app.core.exceptions import NotFoundError
from backend.app.db.session import get_db
from backend.app.models.entities import (
    Application,
    EVC,
    EVCMember,
    Institution,
    RouteStage,
    StageHistory,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.schemas.applications import (
    AdvanceStageRequest,
    ApplicationDetailResponse,
    ApplicationResponse,
    AssignApplicationRequest,
    CreateApplicationRequest,
    HoldStageRequest,
    ResumeStageRequest,
    ReturnStageRequest,
    RouteStageResponse,
    StageHistoryResponse,
)
from backend.app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from backend.app.services.workflow_service import WorkflowService

router = APIRouter()


def apply_application_scoping(stmt, user: User):
    """
    Applies strict server-side institutional, regional, and assignment scoping
    to application queries based on the authenticated user's role.
    """
    role_enum = normalize_role(user.role)

    if role_enum in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.BUREAU_OFFICER, UserRole.SENIOR_AUTHORITY):
        # National administrative and statutory oversight scope
        return stmt

    if role_enum == UserRole.INSTITUTION_USER:
        if not user.institution_id:
            return stmt.where(Application.institution_id.is_(None))
        return stmt.where(Application.institution_id == user.institution_id)

    if role_enum == UserRole.REGIONAL_OFFICER:
        if not user.region_id:
            return stmt.where(Application.institution_id.is_(None))
        return stmt.join(Application.institution).where(Institution.region_id == user.region_id)

    if role_enum == UserRole.COMMITTEE_MEMBER:
        return stmt.join(Application.evcs).join(EVC.members).where(EVCMember.user_id == user.id)

    if role_enum == UserRole.SCRUTINY_OFFICER:
        return stmt

    return stmt


def serialize_application(app: Application, db: Session) -> ApplicationResponse:
    """
    Serializes an Application entity into ApplicationResponse with joined metadata.
    """
    inst = app.institution
    stage = app.current_stage
    route = app.route_type
    assignee = app.assigned_to_user

    total_stages = db.scalar(
        select(func.count(RouteStage.id)).where(
            RouteStage.route_type_id == app.route_type_id,
            RouteStage.route_version == app.route_version,
        )
    ) or 0

    return ApplicationResponse(
        id=app.id,
        reference_no=app.reference_no,
        institution_id=app.institution_id,
        institution_name=inst.name if inst else None,
        institution_code=inst.institution_code if inst else None,
        route_type_id=app.route_type_id,
        route_name=route.name if route else None,
        route_code=route.code if route else None,
        route_version=app.route_version,
        current_stage_id=app.current_stage_id,
        current_stage_name=stage.stage_name if stage else None,
        current_stage_code=stage.stage_code if stage else None,
        current_stage_role=stage.required_role if stage else None,
        current_stage_sequence=stage.sequence if stage else None,
        total_stages=total_stages,
        status=app.status,
        assigned_to_user_id=app.assigned_to_user_id,
        assigned_to_name=assignee.full_name if assignee else None,
        submitted_at=app.submitted_at,
        stage_entered_at=app.stage_entered_at,
        closed_at=app.closed_at,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


def serialize_stage_history(h: StageHistory) -> StageHistoryResponse:
    """
    Serializes a StageHistory record.
    """
    return StageHistoryResponse(
        id=h.id,
        application_id=h.application_id,
        from_stage_id=h.from_stage_id,
        from_stage_name=h.from_stage.stage_name if h.from_stage else None,
        to_stage_id=h.to_stage_id,
        to_stage_name=h.to_stage.stage_name if h.to_stage else None,
        action=h.action,
        reason=h.reason,
        performed_by_user_id=h.performed_by_user_id,
        performed_by_name=h.performed_by.full_name if h.performed_by else None,
        performed_at=h.performed_at,
        metadata=h.metadata_,
    )


@router.get("", response_model=PaginatedResponse[ApplicationResponse], summary="List Scoped Applications")
def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    route_type_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists applications visible to the authenticated user with server-side institutional,
    regional, and assignment scoping, search, and pagination.
    """
    stmt = (
        select(Application)
        .options(
            joinedload(Application.institution),
            joinedload(Application.current_stage),
            joinedload(Application.route_type),
            joinedload(Application.assigned_to_user),
        )
    )

    if status:
        stmt = stmt.where(Application.status == status)
    if route_type_id:
        stmt = stmt.where(Application.route_type_id == route_type_id)
    if search:
        search_filter = f"%{search.strip()}%"
        stmt = stmt.join(Application.institution).where(
            or_(
                Application.reference_no.ilike(search_filter),
                Institution.name.ilike(search_filter),
                Institution.institution_code.ilike(search_filter),
            )
        )

    # Server-side RBAC scoping
    stmt = apply_application_scoping(stmt, current_user)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    offset = (page - 1) * page_size
    items = db.scalars(stmt.order_by(Application.created_at.desc()).offset(offset).limit(page_size)).all()

    return {
        "data": [serialize_application(app, db) for app in items],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=(total + page_size - 1) // page_size if total > 0 else 1,
        ),
    }


@router.post("", response_model=DataResponse[ApplicationResponse], status_code=status.HTTP_201_CREATED, summary="Create Application")
def create_application(
    payload: CreateApplicationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Creates a new application under an authorized institution and pinned route version.
    Protected by Double-Submit Anti-CSRF token verification and RBAC checks.
    """
    app = WorkflowService.create_application(
        db=db,
        user=current_user,
        route_type_id=payload.route_type_id,
        institution_id=payload.institution_id,
    )
    # Refresh relations
    db.refresh(app)
    return {"data": serialize_application(app, db)}


@router.get("/{application_id}", response_model=DataResponse[ApplicationDetailResponse], summary="Get Scoped Application Details")
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves full application details, ordered stages of its pinned route version,
    chronological stage history, and available workflow actions.
    """
    stmt = (
        select(Application)
        .where(Application.id == application_id)
        .options(
            joinedload(Application.institution),
            joinedload(Application.current_stage),
            joinedload(Application.route_type),
            joinedload(Application.assigned_to_user),
        )
    )
    stmt = apply_application_scoping(stmt, current_user)
    app = db.scalars(stmt).first()

    if not app:
        raise NotFoundError("Application not found.")

    stages = WorkflowService.get_route_stages(db, route_type_id=app.route_type_id, route_version=app.route_version)

    history_stmt = (
        select(StageHistory)
        .where(StageHistory.application_id == app.id)
        .options(
            joinedload(StageHistory.from_stage),
            joinedload(StageHistory.to_stage),
            joinedload(StageHistory.performed_by),
        )
        .order_by(StageHistory.performed_at.asc())
    )
    histories = list(db.scalars(history_stmt).all())

    available_actions = WorkflowService.get_available_actions(app, current_user, db)
    base_data = serialize_application(app, db).model_dump()

    detail = ApplicationDetailResponse(
        **base_data,
        stages=[RouteStageResponse.model_validate(s) for s in stages],
        history=[serialize_stage_history(h) for h in histories],
        available_actions=available_actions,
    )
    return {"data": detail}


@router.get("/{application_id}/history", response_model=DataResponse[List[StageHistoryResponse]], summary="Get Application Stage History")
def get_application_history(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the chronological audit history of workflow stage transitions for an authorized application.
    """
    stmt = select(Application).where(Application.id == application_id)
    stmt = apply_application_scoping(stmt, current_user)
    app = db.scalars(stmt).first()
    if not app:
        raise NotFoundError("Application not found.")

    history_stmt = (
        select(StageHistory)
        .where(StageHistory.application_id == app.id)
        .options(
            joinedload(StageHistory.from_stage),
            joinedload(StageHistory.to_stage),
            joinedload(StageHistory.performed_by),
        )
        .order_by(StageHistory.performed_at.asc())
    )
    histories = list(db.scalars(history_stmt).all())
    return {"data": [serialize_stage_history(h) for h in histories]}


@router.post("/{application_id}/advance", response_model=DataResponse[ApplicationResponse], summary="Advance Application Stage")
def advance_application_stage(
    application_id: uuid.UUID,
    payload: AdvanceStageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Advances an application to the next sequential stage in its pinned route version.
    """
    app = WorkflowService.advance_stage(
        db=db,
        application_id=application_id,
        user=current_user,
        comments=payload.comments,
        metadata=payload.metadata,
    )
    return {"data": serialize_application(app, db)}


@router.post("/{application_id}/return", response_model=DataResponse[ApplicationResponse], summary="Return Application Stage")
def return_application_stage(
    application_id: uuid.UUID,
    payload: ReturnStageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Returns an application for deficiency rectification. Mandatory justification reason required.
    """
    app = WorkflowService.return_application(
        db=db,
        application_id=application_id,
        user=current_user,
        reason=payload.reason,
        target_stage_id=payload.target_stage_id,
        metadata=payload.metadata,
    )
    return {"data": serialize_application(app, db)}


@router.post("/{application_id}/hold", response_model=DataResponse[ApplicationResponse], summary="Place Application on Hold")
def hold_application(
    application_id: uuid.UUID,
    payload: HoldStageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Places an active application on hold. Mandatory reason required.
    """
    app = WorkflowService.hold_application(
        db=db,
        application_id=application_id,
        user=current_user,
        reason=payload.reason,
        metadata=payload.metadata,
    )
    return {"data": serialize_application(app, db)}


@router.post("/{application_id}/resume", response_model=DataResponse[ApplicationResponse], summary="Resume Held Application")
def resume_application(
    application_id: uuid.UUID,
    payload: ResumeStageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Resumes an application that is currently on hold.
    """
    app = WorkflowService.resume_application(
        db=db,
        application_id=application_id,
        user=current_user,
        comments=payload.comments,
        metadata=payload.metadata,
    )
    return {"data": serialize_application(app, db)}


@router.post("/{application_id}/assign", response_model=DataResponse[ApplicationResponse], summary="Assign Application to Officer")
def assign_application(
    application_id: uuid.UUID,
    payload: AssignApplicationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Assigns or reassigns an application to an active reviewer, validating regional jurisdiction.
    """
    app = WorkflowService.assign_application(
        db=db,
        application_id=application_id,
        user=current_user,
        target_user_id=payload.target_user_id,
        notes=payload.notes,
    )
    return {"data": serialize_application(app, db)}
