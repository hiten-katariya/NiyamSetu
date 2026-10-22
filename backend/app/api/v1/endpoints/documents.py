from datetime import date
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, verify_csrf_token
from backend.app.core.exceptions import ForbiddenError, NotFoundError
from backend.app.db.session import get_db
from backend.app.models.entities import (
    Application,
    Document,
    DocumentRenewal,
    FileRecord,
    Institution,
    User,
)
from backend.app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from backend.app.schemas.documents import (
    CreateRenewalRequest,
    DocumentRenewalResponse,
    DocumentResponse,
    VerifyDocumentRequest,
)
from backend.app.services.document_service import DocumentService
from backend.app.services.file_service import FileStorageService

router = APIRouter()


def serialize_document(doc: Document) -> DocumentResponse:
    app_no = doc.application.reference_no if doc.application else None
    inst_name = doc.institution.name if doc.institution else None
    verifier_name = doc.verified_by.full_name if doc.verified_by else None

    is_expired, is_expiring_soon = DocumentService.compute_validity_state(doc)

    renewals_list = [
        DocumentRenewalResponse(
            id=r.id,
            document_id=r.document_id,
            renewal_due_date=r.renewal_due_date,
            status=r.status,
            replacement_document_id=r.replacement_document_id,
            replacement_filename=(
                r.replacement_document.original_filename
                if r.replacement_document
                else None
            ),
            reviewed_by_user_id=r.reviewed_by_user_id,
            reviewed_by_name=r.reviewed_by.full_name if r.reviewed_by else None,
            reviewed_at=r.reviewed_at,
            created_at=r.created_at,
        )
        for r in (doc.renewals or [])
    ]

    return DocumentResponse(
        id=doc.id,
        institution_id=doc.institution_id,
        institution_name=inst_name,
        application_id=doc.application_id,
        application_number=app_no,
        document_type=doc.document_type,
        original_filename=doc.original_filename,
        size_bytes=doc.size_bytes,
        mime_type=doc.mime_type,
        checksum=doc.checksum,
        valid_from=doc.valid_from,
        valid_to=doc.valid_to,
        is_expired=is_expired,
        is_expiring_soon=is_expiring_soon,
        verification_status=doc.verification_status,
        verified_by_user_id=doc.verified_by_user_id,
        verified_by_name=verifier_name,
        verified_at=doc.verified_at,
        created_by_user_id=doc.created_by_user_id,
        created_at=doc.created_at,
        renewals=renewals_list,
    )


@router.get("", response_model=PaginatedResponse[DocumentResponse], summary="List Compliance Documents")
def list_documents(
    document_type: Optional[str] = Query(None),
    institution_id: Optional[uuid.UUID] = Query(None),
    application_id: Optional[uuid.UUID] = Query(None),
    verification_status: Optional[str] = Query(None),
    expiry_filter: Optional[str] = Query(None, description="valid, expiring_soon, expired"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Document)
        .options(
            joinedload(Document.institution),
            joinedload(Document.application),
            joinedload(Document.verified_by),
            joinedload(Document.renewals).joinedload(DocumentRenewal.replacement_document),
            joinedload(Document.renewals).joinedload(DocumentRenewal.reviewed_by),
        )
    )
    stmt = DocumentService.apply_document_scoping(stmt, current_user)

    if document_type:
        stmt = stmt.where(Document.document_type == document_type)
    if institution_id:
        stmt = stmt.where(Document.institution_id == institution_id)
    if application_id:
        stmt = stmt.where(Document.application_id == application_id)
    if verification_status:
        stmt = stmt.where(Document.verification_status == verification_status)

    today = date.today()
    if expiry_filter == "expired":
        stmt = stmt.where(Document.valid_to < today)
    elif expiry_filter == "expiring_soon":
        stmt = stmt.where(Document.valid_to >= today, Document.valid_to <= today + (30 * 86400))
    elif expiry_filter == "valid":
        stmt = stmt.where(Document.valid_to >= today)

    total_items = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    total_pages = max(1, (total_items + limit - 1) // limit)
    offset = (page - 1) * limit

    records = list(
        db.scalars(
            stmt.order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).unique().all()
    )

    return {
        "data": [serialize_document(d) for d in records],
        "meta": PaginationMeta(
            page=page,
            page_size=limit,
            total=total_items,
            total_pages=total_pages,
        ),
    }


@router.get("/{document_id}", response_model=DataResponse[DocumentResponse], summary="Get Document Details")
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = DocumentService.get_document(db, document_id, current_user)
    return {"data": serialize_document(doc)}


@router.get("/{document_id}/download", summary="Securely Download Document File")
def download_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Secure file download endpoint.
    Enforces server-side authorization and prevents public exposure or path traversal.
    """
    doc = DocumentService.get_document(db, document_id, current_user)

    file_record = db.scalar(select(FileRecord).where(FileRecord.storage_key == doc.storage_key))
    if not file_record:
        raise NotFoundError("File metadata not found.")

    file_path = FileStorageService.get_file_path(file_record)

    return FileResponse(
        path=str(file_path),
        media_type=doc.mime_type,
        filename=doc.original_filename,
    )


@router.post("", response_model=DataResponse[DocumentResponse], summary="Upload Compliance Document")
def upload_document(
    institution_id: uuid.UUID = Form(...),
    document_type: str = Form(...),
    application_id: Optional[uuid.UUID] = Form(None),
    valid_from: Optional[date] = Form(None),
    valid_to: Optional[date] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    file_record = FileStorageService.save_upload_file(db=db, file=file, uploaded_by=current_user)
    doc = DocumentService.upload_document(
        db=db,
        institution_id=institution_id,
        document_type=document_type,
        file_record=file_record,
        user=current_user,
        application_id=application_id,
        valid_from=valid_from,
        valid_to=valid_to,
    )
    doc = DocumentService.get_document(db, doc.id, current_user)
    return {"data": serialize_document(doc)}


@router.post("/{document_id}/verify", response_model=DataResponse[DocumentResponse], summary="Verify Document Compliance")
def verify_document(
    document_id: uuid.UUID,
    payload: VerifyDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    doc = DocumentService.verify_document(
        db=db,
        document_id=document_id,
        decision=payload.decision,
        review_comments=payload.review_comments,
        user=current_user,
    )
    doc = DocumentService.get_document(db, doc.id, current_user)
    return {"data": serialize_document(doc)}


@router.post("/{document_id}/renew", response_model=DataResponse[DocumentRenewalResponse], summary="Create Renewal Obligation")
def create_document_renewal(
    document_id: uuid.UUID,
    payload: CreateRenewalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    renewal = DocumentService.create_renewal(
        db=db,
        document_id=document_id,
        renewal_due_date=payload.renewal_due_date,
        user=current_user,
    )
    return {
        "data": DocumentRenewalResponse(
            id=renewal.id,
            document_id=renewal.document_id,
            renewal_due_date=renewal.renewal_due_date,
            status=renewal.status,
            created_at=renewal.created_at,
        )
    }


@router.post("/renewals/{renewal_id}/replace", response_model=DataResponse[DocumentResponse], summary="Upload Replacement Document for Renewal")
def replace_document_renewal(
    renewal_id: uuid.UUID,
    valid_from: Optional[date] = Form(None),
    valid_to: Optional[date] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_csrf_token),
):
    file_record = FileStorageService.save_upload_file(db=db, file=file, uploaded_by=current_user)
    new_doc = DocumentService.upload_replacement_document(
        db=db,
        renewal_id=renewal_id,
        file_record=file_record,
        valid_from=valid_from,
        valid_to=valid_to,
        user=current_user,
    )
    new_doc = DocumentService.get_document(db, new_doc.id, current_user)
    return {"data": serialize_document(new_doc)}
