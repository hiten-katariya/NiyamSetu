from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.core.exceptions import AppException, ForbiddenError, NotFoundError
from backend.app.models.entities import (
    Application,
    Document,
    DocumentRenewal,
    FileRecord,
    Institution,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.services.audit_service import AuditService


class DocumentService:
    """
    Document Validity & Lease Renewal Engine.
    Tracks expiration dates, renewals, replacements, and authorized compliance verifications.
    """

    @classmethod
    def apply_document_scoping(cls, stmt, user: User):
        """
        Applies strict server-side institutional and regional scoping to document queries.
        """
        role_enum = normalize_role(user.role)

        if role_enum in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.BUREAU_OFFICER, UserRole.SENIOR_AUTHORITY):
            return stmt

        if role_enum == UserRole.INSTITUTION_USER:
            if not user.institution_id:
                return stmt.where(Document.id == None)
            return stmt.where(Document.institution_id == user.institution_id)

        if role_enum == UserRole.REGIONAL_OFFICER:
            if not user.region_id:
                return stmt.where(Document.id == None)
            return stmt.join(Document.institution).where(Institution.region_id == user.region_id)

        return stmt

    @classmethod
    def compute_validity_state(cls, doc: Document) -> Tuple[bool, bool]:
        """
        Computes dynamic validity indicators: (is_expired, is_expiring_soon).
        Expiring soon is triggered if valid_to is within the next 30 calendar days.
        """
        if not doc.valid_to:
            return False, False

        today = date.today()
        is_expired = doc.valid_to < today
        is_expiring_soon = not is_expired and (doc.valid_to <= today + timedelta(days=30))
        return is_expired, is_expiring_soon

    @classmethod
    def get_document(cls, db: Session, document_id: uuid.UUID, user: User) -> Document:
        """
        Retrieves a single document, verifying user authorization and data scoping.
        """
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(
                joinedload(Document.institution),
                joinedload(Document.application),
                joinedload(Document.verified_by),
                joinedload(Document.renewals).joinedload(DocumentRenewal.replacement_document),
                joinedload(Document.renewals).joinedload(DocumentRenewal.reviewed_by),
            )
        )
        stmt = cls.apply_document_scoping(stmt, user)
        doc = db.scalars(stmt).unique().first()
        if not doc:
            raise NotFoundError("Document not found or inaccessible.")
        return doc

    @classmethod
    def upload_document(
        cls,
        db: Session,
        institution_id: uuid.UUID,
        document_type: str,
        file_record: FileRecord,
        user: User,
        application_id: Optional[uuid.UUID] = None,
        valid_from: Optional[date] = None,
        valid_to: Optional[date] = None,
    ) -> Document:
        """
        Registers a new compliance document or lease agreement.
        Validates date consistency: valid_from must precede or equal valid_to.
        """
        role_enum = normalize_role(user.role)
        if role_enum == UserRole.INSTITUTION_USER:
            if user.institution_id != institution_id:
                raise ForbiddenError("Cannot upload documents for another institution.")

        if valid_from and valid_to and valid_from > valid_to:
            raise AppException("valid_from date cannot be later than valid_to date.", code="INVALID_DATE_RANGE", status_code=400)

        doc = Document(
            id=uuid.uuid4(),
            institution_id=institution_id,
            application_id=application_id,
            document_type=document_type.strip(),
            original_filename=file_record.original_filename,
            storage_key=file_record.storage_key,
            mime_type=file_record.mime_type,
            size_bytes=file_record.size_bytes,
            checksum=file_record.checksum,
            valid_from=valid_from,
            valid_to=valid_to,
            verification_status="pending",
            created_by_user_id=user.id,
        )
        db.add(doc)

        AuditService.record_action(
            db=db,
            action="DOCUMENT_UPLOADED",
            entity_type="document",
            entity_id=str(doc.id),
            actor_user_id=user.id,
            metadata={
                "document_type": document_type,
                "valid_from": valid_from.isoformat() if valid_from else None,
                "valid_to": valid_to.isoformat() if valid_to else None,
                "checksum": file_record.checksum,
            },
        )

        db.commit()
        db.refresh(doc)
        return doc

    @classmethod
    def verify_document(
        cls,
        db: Session,
        document_id: uuid.UUID,
        decision: str,
        review_comments: str,
        user: User,
    ) -> Document:
        """
        Authorised verification of a compliance document.
        Institution users are forbidden from self-verifying documents.
        """
        role_enum = normalize_role(user.role)
        if role_enum == UserRole.INSTITUTION_USER:
            raise ForbiddenError("Institution users cannot verify documents.")

        doc = cls.get_document(db, document_id, user)

        if not review_comments or not review_comments.strip():
            raise AppException("Review comments are mandatory.", code="COMMENTS_REQUIRED", status_code=422)

        now = datetime.now(timezone.utc)
        doc.verification_status = decision
        doc.verified_by_user_id = user.id
        doc.verified_at = now

        AuditService.record_action(
            db=db,
            action="DOCUMENT_VERIFIED",
            entity_type="document",
            entity_id=str(doc.id),
            actor_user_id=user.id,
            metadata={"decision": decision, "comments": review_comments.strip()},
        )

        db.commit()
        db.refresh(doc)
        return doc

    @classmethod
    def create_renewal(
        cls,
        db: Session,
        document_id: uuid.UUID,
        renewal_due_date: date,
        user: User,
    ) -> DocumentRenewal:
        """
        Creates an upcoming renewal obligation linked to an existing document.
        """
        doc = cls.get_document(db, document_id, user)

        renewal = DocumentRenewal(
            id=uuid.uuid4(),
            document_id=doc.id,
            renewal_due_date=renewal_due_date,
            status="pending",
        )
        db.add(renewal)

        AuditService.record_action(
            db=db,
            action="DOCUMENT_RENEWAL_CREATED",
            entity_type="document_renewal",
            entity_id=str(renewal.id),
            actor_user_id=user.id,
            metadata={"document_id": str(doc.id), "renewal_due_date": renewal_due_date.isoformat()},
        )

        db.commit()
        db.refresh(renewal)
        return renewal

    @classmethod
    def upload_replacement_document(
        cls,
        db: Session,
        renewal_id: uuid.UUID,
        file_record: FileRecord,
        valid_from: Optional[date],
        valid_to: Optional[date],
        user: User,
    ) -> Document:
        """
        Uploads a replacement document fulfilling an active renewal.
        Preserves the previous document and full version history without destructive overwriting.
        """
        renewal = db.get(DocumentRenewal, renewal_id)
        if not renewal:
            raise NotFoundError("Renewal record not found.")

        old_doc = cls.get_document(db, renewal.document_id, user)

        # Create new replacement document
        new_doc = cls.upload_document(
            db=db,
            institution_id=old_doc.institution_id,
            document_type=old_doc.document_type,
            file_record=file_record,
            user=user,
            application_id=old_doc.application_id,
            valid_from=valid_from,
            valid_to=valid_to,
        )

        now = datetime.now(timezone.utc)
        renewal.replacement_document_id = new_doc.id
        renewal.status = "completed"
        renewal.reviewed_by_user_id = user.id
        renewal.reviewed_at = now

        AuditService.record_action(
            db=db,
            action="DOCUMENT_RENEWAL_COMPLETED",
            entity_type="document_renewal",
            entity_id=str(renewal.id),
            actor_user_id=user.id,
            metadata={
                "previous_document_id": str(old_doc.id),
                "replacement_document_id": str(new_doc.id),
            },
        )

        db.commit()
        db.refresh(new_doc)
        return new_doc
