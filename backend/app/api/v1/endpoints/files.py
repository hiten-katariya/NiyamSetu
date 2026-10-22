import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.exceptions import ForbiddenError, NotFoundError
from backend.app.db.session import get_db
from backend.app.models.entities import (
    Application,
    Document,
    EVC,
    EVCMember,
    EVCReport,
    FileRecord,
    Institution,
    Undertaking,
    UndertakingSubmission,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.services.file_service import FileStorageService

router = APIRouter()


@router.get("/{file_id}/download", summary="Download File with Resource Authorization")
def download_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Authorized file download endpoint.
    Verifies that the user has legitimate access to the linked resource
    (EVC Report, Undertaking Submission, or Document).
    """
    file_record = db.get(FileRecord, file_id)
    if not file_record:
        raise NotFoundError("File not found.")

    role_enum = normalize_role(current_user.role)

    # Admins and Senior Authorities have global oversight access
    if role_enum not in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.SENIOR_AUTHORITY, UserRole.BUREAU_OFFICER):
        # 1. Check if user is the direct uploader
        is_uploader = file_record.uploaded_by_user_id == current_user.id

        # 2. Check if linked to an EVC Report
        evc_report = db.scalar(select(EVCReport).where(EVCReport.file_id == file_id))
        has_evc_access = False
        if evc_report:
            evc = db.get(EVC, evc_report.evc_id)
            if evc:
                if role_enum == UserRole.REGIONAL_OFFICER and evc.assigned_region_id == current_user.region_id:
                    has_evc_access = True
                elif role_enum == UserRole.COMMITTEE_MEMBER:
                    is_member = db.scalar(
                        select(EVCMember.id).where(
                            EVCMember.evc_id == evc.id,
                            EVCMember.user_id == current_user.id,
                        )
                    )
                    if is_member:
                        has_evc_access = True
                elif role_enum == UserRole.INSTITUTION_USER:
                    app = db.get(Application, evc.application_id)
                    if app and app.institution_id == current_user.institution_id:
                        has_evc_access = True

        # 3. Check if linked to an Undertaking Submission
        undertaking_sub = db.scalar(select(UndertakingSubmission).where(UndertakingSubmission.file_id == file_id))
        has_undertaking_access = False
        if undertaking_sub:
            u = db.get(Undertaking, undertaking_sub.undertaking_id)
            if u:
                if role_enum == UserRole.INSTITUTION_USER and u.assigned_institution_id == current_user.institution_id:
                    has_undertaking_access = True
                elif role_enum == UserRole.REGIONAL_OFFICER:
                    inst = db.get(Institution, u.assigned_institution_id)
                    if inst and inst.region_id == current_user.region_id:
                        has_undertaking_access = True
                elif role_enum == UserRole.SCRUTINY_OFFICER:
                    has_undertaking_access = True

        # 4. Check if linked to a Document
        doc = db.scalar(select(Document).where(Document.storage_key == file_record.storage_key))
        has_doc_access = False
        if doc:
            if role_enum == UserRole.INSTITUTION_USER and doc.institution_id == current_user.institution_id:
                has_doc_access = True
            elif role_enum == UserRole.REGIONAL_OFFICER:
                inst = db.get(Institution, doc.institution_id)
                if inst and inst.region_id == current_user.region_id:
                    has_doc_access = True
            elif role_enum == UserRole.SCRUTINY_OFFICER:
                has_doc_access = True

        if not (is_uploader or has_evc_access or has_undertaking_access or has_doc_access):
            raise ForbiddenError("You are not authorized to download this file.")

    file_path = FileStorageService.get_file_path(file_record)

    return FileResponse(
        path=str(file_path),
        media_type=file_record.mime_type,
        filename=file_record.original_filename,
    )
