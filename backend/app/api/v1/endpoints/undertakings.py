from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, verify_csrf_token
from backend.app.db.session import get_db
from backend.app.models.entities import (
    Application,
    Institution,
    Undertaking,
    UndertakingSubmission,
    User,
)
from backend.app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from backend.app.schemas.undertakings import (
    CreateUndertakingRequest,
    ReviewUndertakingRequest,
    UndertakingResponse,
    UndertakingSubmissionResponse,
)
from backend.app.services.file_service import FileStorageService
from backend.app.services.undertaking_service import UndertakingService

router = APIRouter()


def serialize_undertaking(u: Undertaking) -> UndertakingResponse:
    app_no = u.application.reference_no if u.application else None
    inst_name = u.institution.name if u.institution else None
    verifier_name = u.verified_by.full_name if u.verified_by else None

    submissions_list = [
        UndertakingSubmissionResponse(
            id=s.id,
            undertaking_id=s.undertaking_id,
            submitted_by_user_id=s.submitted_by_user_id,
            submitted_by_name=s.submitted_by.full_name if s.submitted_by else None,
            file_id=s.file_id,
            original_filename=s.file.original_filename if s.file else None,
            comments=s.comments,
            submitted_at=s.submitted_at,
            review_status=s.review_status,
            reviewed_by_user_id=s.reviewed_by_user_id,
            reviewed_by_name=s.reviewed_by.full_name if s.reviewed_by else None,
            reviewed_at=s.reviewed_at,
            review_comments=s.review_comments,
        )
        for s in (u.submissions or [])
    ]

    return UndertakingResponse(
        id=u.id,
        application_id=u.application_id,
        application_number=app_no,
        institution_id=u.assigned_institution_id,
        institution_name=inst_name,
        title=u.title,
        description=u.description,
        due_date=u.due_date,
        status=u.status,
        verified_by_user_id=u.verified_by_user_id,
        verified_by_name=verifier_name,
        verified_at=u.verified_at,
        verification_notes=u.verification_notes,
        submissions=submissions_list,
        created_at=u.created_at,
        updated_at=u.updated_at,
    )


@router.get("", response_model=PaginatedResponse[UndertakingResponse], summary="List Undertakings")
def list_undertakings(
    status_filter: Optional[str] = Query(None, alias="status"),
    institution_id: Optional[uuid.UUID] = Query(None),
    application_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Undertaking)
        .options(
            joinedload(Undertaking.application),
            joinedload(Undertaking.institution),
            joinedload(Undertaking.verified_by),
            joinedload(Undertaking.submissions).joinedload(UndertakingSubmission.file),
            joinedload(Undertaking.submissions).joinedload(UndertakingSubmission.submitted_by),
        )
    )
    stmt = UndertakingService.apply_undertaking_scoping(stmt, current_user)

    if status_filter:
        stmt = stmt.where(Undertaking.status == status_filter)
    if institution_id:
        stmt = stmt.where(Undertaking.assigned_institution_id == institution_id)
    if application_id:
        stmt = stmt.where(Undertaking.application_id == application_id)

    total_items = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    total_pages = max(1, (total_items + limit - 1) // limit)
    offset = (page - 1) * limit

    records = list(
        db.scalars(
            stmt.order_by(Undertaking.due_date.asc(), Undertaking.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).unique().all()
    )

    return {
        "data": [serialize_undertaking(u) for u in records],
        "meta": PaginationMeta(
            page=page,
            page_size=limit,
            total=total_items,
            total_pages=total_pages,
        ),
    }


@router.get("/{undertaking_id}", response_model=DataResponse[UndertakingResponse], summary="Get Undertaking Details")
def get_undertaking(
    undertaking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    u = UndertakingService.get_undertaking(db, undertaking_id, current_user)
    return {"data": serialize_undertaking(u)}


@router.post("", response_model=DataResponse[UndertakingResponse], summary="Create Undertaking Obligation")
def create_undertaking(
    payload: CreateUndertakingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    u = UndertakingService.create_undertaking(
        db=db,
        application_id=payload.application_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        user=current_user,
        assigned_institution_id=payload.assigned_institution_id,
    )
    u = UndertakingService.get_undertaking(db, u.id, current_user)
    return {"data": serialize_undertaking(u)}


@router.post("/{undertaking_id}/submit", response_model=DataResponse[UndertakingSubmissionResponse], summary="Submit Evidence for Undertaking")
def submit_undertaking_evidence(
    undertaking_id: uuid.UUID,
    file: UploadFile = File(...),
    comments: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    file_record = FileStorageService.save_upload_file(db=db, file=file, uploaded_by=current_user)
    sub = UndertakingService.submit_evidence(
        db=db,
        undertaking_id=undertaking_id,
        file_id=file_record.id,
        user=current_user,
        comments=comments,
    )
    return {
        "data": UndertakingSubmissionResponse(
            id=sub.id,
            undertaking_id=sub.undertaking_id,
            submitted_by_user_id=sub.submitted_by_user_id,
            submitted_by_name=current_user.full_name,
            file_id=sub.file_id,
            original_filename=file_record.original_filename,
            comments=sub.comments,
            submitted_at=sub.submitted_at,
            review_status=sub.review_status,
        )
    }


@router.post("/submissions/{submission_id}/review", response_model=DataResponse[UndertakingSubmissionResponse], summary="Review Undertaking Evidence")
def review_undertaking_submission(
    submission_id: uuid.UUID,
    payload: ReviewUndertakingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    sub = UndertakingService.review_submission(
        db=db,
        submission_id=submission_id,
        decision=payload.decision,
        review_comments=payload.review_comments,
        user=current_user,
    )
    return {
        "data": UndertakingSubmissionResponse(
            id=sub.id,
            undertaking_id=sub.undertaking_id,
            submitted_by_user_id=sub.submitted_by_user_id,
            submitted_at=sub.submitted_at,
            review_status=sub.review_status,
            reviewed_by_user_id=sub.reviewed_by_user_id,
            reviewed_by_name=current_user.full_name,
            reviewed_at=sub.reviewed_at,
            review_comments=sub.review_comments,
            file_id=sub.file_id,
        )
    }
