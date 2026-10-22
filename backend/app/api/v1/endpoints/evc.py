from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, verify_csrf_token
from backend.app.db.session import get_db
from backend.app.models.entities import (
    Application,
    EVC,
    EVCMember,
    EVCReport,
    Institution,
    Region,
    User,
)
from backend.app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from backend.app.schemas.evc import (
    AssignEVCMembersRequest,
    ConductEVCRequest,
    CreateEVCRequest,
    EVCMemberSchema,
    EVCReportResponse,
    EVCResponse,
    ReviewEVCReportRequest,
    ScheduleEVCRequest,
)
from backend.app.services.evc_service import EVCService
from backend.app.services.file_service import FileStorageService

router = APIRouter()


def serialize_evc(evc: EVC) -> EVCResponse:
    app_no = evc.application.reference_no if evc.application else None
    inst_name = (
        evc.application.institution.name
        if evc.application and evc.application.institution
        else None
    )
    reg_name = evc.assigned_region.name if evc.assigned_region else None

    members_list = [
        EVCMemberSchema(
            id=m.id,
            evc_id=m.evc_id,
            user_id=m.user_id,
            member_name=m.member_name,
            member_role=m.member_role,
            created_at=m.created_at,
        )
        for m in (evc.members or [])
    ]

    reports_list = [
        EVCReportResponse(
            id=r.id,
            evc_id=r.evc_id,
            file_id=r.file_id,
            original_filename=r.file.original_filename if r.file else None,
            submitted_by_user_id=r.submitted_by_user_id,
            submitted_by_name=r.submitted_by.full_name if r.submitted_by else None,
            submitted_at=r.submitted_at,
            review_status=r.review_status,
            reviewed_by_user_id=r.reviewed_by_user_id,
            reviewed_by_name=r.reviewed_by.full_name if r.reviewed_by else None,
            reviewed_at=r.reviewed_at,
            review_comments=r.review_comments,
        )
        for r in (evc.reports or [])
    ]

    return EVCResponse(
        id=evc.id,
        application_id=evc.application_id,
        application_number=app_no,
        institution_name=inst_name,
        status=evc.status,
        scheduled_at=evc.scheduled_at,
        due_by=evc.due_by,
        conducted_at=evc.conducted_at,
        report_due_by=evc.report_due_by,
        report_submitted_at=evc.report_submitted_at,
        assigned_region_id=evc.assigned_region_id,
        assigned_region_name=reg_name,
        notes=evc.notes,
        members=members_list,
        reports=reports_list,
        created_at=evc.created_at,
        updated_at=evc.updated_at,
    )


@router.get("", response_model=PaginatedResponse[EVCResponse], summary="List EVC Visits")
def list_evcs(
    status_filter: Optional[str] = Query(None, alias="status"),
    region_id: Optional[uuid.UUID] = Query(None),
    application_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists EVC records strictly scoped to the user's role and regional jurisdiction.
    """
    stmt = (
        select(EVC)
        .options(
            joinedload(EVC.application).joinedload(Application.institution),
            joinedload(EVC.assigned_region),
            joinedload(EVC.members),
            joinedload(EVC.reports).joinedload(EVCReport.file),
        )
    )
    stmt = EVCService.apply_evc_scoping(stmt, current_user)

    if status_filter:
        stmt = stmt.where(EVC.status == status_filter)
    if region_id:
        stmt = stmt.where(EVC.assigned_region_id == region_id)
    if application_id:
        stmt = stmt.where(EVC.application_id == application_id)

    total_items = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    total_pages = max(1, (total_items + limit - 1) // limit)
    offset = (page - 1) * limit

    records = list(
        db.scalars(
            stmt.order_by(EVC.scheduled_at.desc().nullslast(), EVC.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).unique().all()
    )

    return {
        "data": [serialize_evc(e) for e in records],
        "meta": PaginationMeta(
            page=page,
            page_size=limit,
            total=total_items,
            total_pages=total_pages,
        ),
    }


@router.get("/{evc_id}", response_model=DataResponse[EVCResponse], summary="Get EVC Details")
def get_evc(
    evc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evc = EVCService.get_evc(db, evc_id, current_user)
    return {"data": serialize_evc(evc)}


@router.post("", response_model=DataResponse[EVCResponse], summary="Create or Queue EVC")
def create_evc(
    payload: CreateEVCRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    evc = EVCService.create_evc(
        db=db,
        application_id=payload.application_id,
        user=current_user,
        due_by=payload.due_by,
        notes=payload.notes,
    )
    evc = EVCService.get_evc(db, evc.id, current_user)
    return {"data": serialize_evc(evc)}


@router.post("/{evc_id}/schedule", response_model=DataResponse[EVCResponse], summary="Schedule / Reschedule EVC Visit")
def schedule_evc(
    evc_id: uuid.UUID,
    payload: ScheduleEVCRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    evc = EVCService.schedule_evc(
        db=db,
        evc_id=evc_id,
        user=current_user,
        scheduled_at=payload.scheduled_at,
        notes=payload.notes,
        reason=payload.reason,
    )
    evc = EVCService.get_evc(db, evc.id, current_user)
    return {"data": serialize_evc(evc)}


@router.post("/{evc_id}/members", response_model=DataResponse[EVCResponse], summary="Assign Committee Members")
def assign_evc_members(
    evc_id: uuid.UUID,
    payload: AssignEVCMembersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    members_dicts = [m.model_dump() for m in payload.members]
    evc = EVCService.assign_members(
        db=db,
        evc_id=evc_id,
        user=current_user,
        members_data=members_dicts,
    )
    evc = EVCService.get_evc(db, evc.id, current_user)
    return {"data": serialize_evc(evc)}


@router.post("/{evc_id}/conduct", response_model=DataResponse[EVCResponse], summary="Record EVC Visit Conduct")
def conduct_evc(
    evc_id: uuid.UUID,
    payload: ConductEVCRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    evc = EVCService.conduct_evc(
        db=db,
        evc_id=evc_id,
        user=current_user,
        conducted_at=payload.conducted_at,
        notes=payload.notes,
    )
    evc = EVCService.get_evc(db, evc.id, current_user)
    return {"data": serialize_evc(evc)}


@router.post("/{evc_id}/report", response_model=DataResponse[EVCReportResponse], summary="Upload & Submit EVC Report")
def submit_evc_report(
    evc_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    file_record = FileStorageService.save_upload_file(db=db, file=file, uploaded_by=current_user)
    report = EVCService.submit_report(
        db=db,
        evc_id=evc_id,
        user=current_user,
        file_id=file_record.id,
    )
    return {
        "data": EVCReportResponse(
            id=report.id,
            evc_id=report.evc_id,
            file_id=report.file_id,
            original_filename=file_record.original_filename,
            submitted_by_user_id=report.submitted_by_user_id,
            submitted_by_name=current_user.full_name,
            submitted_at=report.submitted_at,
            review_status=report.review_status,
        )
    }


@router.post("/reports/{report_id}/review", response_model=DataResponse[EVCReportResponse], summary="Review EVC Report")
def review_evc_report(
    report_id: uuid.UUID,
    payload: ReviewEVCReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    report = EVCService.review_report(
        db=db,
        report_id=report_id,
        user=current_user,
        decision=payload.decision,
        review_comments=payload.review_comments,
    )
    return {
        "data": EVCReportResponse(
            id=report.id,
            evc_id=report.evc_id,
            file_id=report.file_id,
            submitted_by_user_id=report.submitted_by_user_id,
            submitted_at=report.submitted_at,
            review_status=report.review_status,
            reviewed_by_user_id=report.reviewed_by_user_id,
            reviewed_by_name=current_user.full_name,
            reviewed_at=report.reviewed_at,
            review_comments=report.review_comments,
        )
    }
