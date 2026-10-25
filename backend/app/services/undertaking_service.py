from datetime import date, datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.core.exceptions import AppException, BadRequestError, ForbiddenError, NotFoundError
from backend.app.models.entities import (
    Application,
    Institution,
    Undertaking,
    UndertakingSubmission,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.services.audit_service import AuditService


class UndertakingService:
    """
    Time-Bound Undertaking Compliance Service.
    Enforces dual-control verification, strict institutional boundaries, and immutable audit logs.
    """

    @classmethod
    def apply_undertaking_scoping(cls, stmt, user: User):
        """
        Applies role and institution scoping to Undertaking queries.
        """
        role_enum = normalize_role(user.role)

        if role_enum in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.BUREAU_OFFICER, UserRole.SENIOR_AUTHORITY):
            return stmt

        if role_enum == UserRole.INSTITUTION_USER:
            if not user.institution_id:
                return stmt.where(Undertaking.id == None)
            return stmt.where(Undertaking.assigned_institution_id == user.institution_id)

        if role_enum == UserRole.REGIONAL_OFFICER:
            if not user.region_id:
                return stmt.where(Undertaking.id == None)
            return stmt.join(Undertaking.institution).where(Institution.region_id == user.region_id)

        return stmt

    @classmethod
    def get_undertaking(cls, db: Session, undertaking_id: uuid.UUID, user: User) -> Undertaking:
        """
        Retrieves an undertaking and its submission history, checking permissions.
        """
        stmt = (
            select(Undertaking)
            .where(Undertaking.id == undertaking_id)
            .options(
                joinedload(Undertaking.application),
                joinedload(Undertaking.institution),
                joinedload(Undertaking.verified_by),
                joinedload(Undertaking.submissions).joinedload(UndertakingSubmission.file),
                joinedload(Undertaking.submissions).joinedload(UndertakingSubmission.submitted_by),
                joinedload(Undertaking.submissions).joinedload(UndertakingSubmission.reviewed_by),
            )
        )
        stmt = cls.apply_undertaking_scoping(stmt, user)
        u = db.scalars(stmt).unique().first()
        if not u:
            raise NotFoundError("Undertaking not found or inaccessible.")
        return u

    @classmethod
    def create_undertaking(
        cls,
        db: Session,
        application_id: Optional[uuid.UUID],
        title: str,
        description: str,
        due_date: date,
        user: User,
        assigned_institution_id: Optional[uuid.UUID] = None,
    ) -> Undertaking:
        """
        Creates a new statutory or conditional undertaking.
        Restricted to regional, scrutiny, and administrative officers.
        """
        role_enum = normalize_role(user.role)
        if role_enum == UserRole.INSTITUTION_USER:
            raise ForbiddenError("Institution users cannot create undertakings.")

        if not application_id:
            stmt = select(Application)
            if assigned_institution_id:
                stmt = stmt.where(Application.institution_id == assigned_institution_id)
            elif role_enum == UserRole.REGIONAL_OFFICER and user.region_id:
                stmt = stmt.join(Institution).where(Institution.region_id == user.region_id)
            elif role_enum == UserRole.INSTITUTION_USER and user.institution_id:
                stmt = stmt.where(Application.institution_id == user.institution_id)
            app = db.scalars(stmt.order_by(Application.created_at.desc())).first()
            if not app:
                raise BadRequestError("An application must be selected to issue an undertaking.")
            application_id = app.id
        else:
            app = db.get(Application, application_id)
            if not app:
                raise NotFoundError("Application not found.")

        target_inst_id = assigned_institution_id or app.institution_id

        # Regional officer scoping check
        if role_enum == UserRole.REGIONAL_OFFICER:
            inst = app.institution or db.get(Institution, app.institution_id)
            if inst and inst.region_id and inst.region_id != user.region_id:
                raise ForbiddenError("Cannot create undertakings for institutions outside your regional jurisdiction.")

        undertaking = Undertaking(
            id=uuid.uuid4(),
            application_id=app.id,
            title=title.strip(),
            description=description.strip(),
            due_date=due_date,
            status="pending",
            assigned_institution_id=target_inst_id,
        )
        db.add(undertaking)

        AuditService.record_action(
            db=db,
            action="UNDERTAKING_CREATED",
            entity_type="undertaking",
            entity_id=str(undertaking.id),
            actor_user_id=user.id,
            metadata={"application_id": str(app.id), "due_date": due_date.isoformat(), "title": title},
        )

        db.commit()
        db.refresh(undertaking)
        return undertaking

    @classmethod
    def submit_evidence(
        cls,
        db: Session,
        undertaking_id: uuid.UUID,
        file_id: uuid.UUID,
        user: User,
        comments: Optional[str] = None,
    ) -> UndertakingSubmission:
        """
        Submits evidence/proof for an undertaking obligation.
        Strictly restricted to users belonging to the assigned institution.
        """
        undertaking = cls.get_undertaking(db, undertaking_id, user)

        role_enum = normalize_role(user.role)
        if role_enum == UserRole.INSTITUTION_USER:
            if user.institution_id != undertaking.assigned_institution_id:
                raise ForbiddenError("Cannot submit evidence for an undertaking belonging to another institution.")

        now = datetime.now(timezone.utc)
        sub = UndertakingSubmission(
            id=uuid.uuid4(),
            undertaking_id=undertaking.id,
            submitted_by_user_id=user.id,
            file_id=file_id,
            comments=comments.strip() if comments else None,
            submitted_at=now,
            review_status="pending",
        )
        db.add(sub)

        undertaking.status = "submitted"

        AuditService.record_action(
            db=db,
            action="UNDERTAKING_EVIDENCE_SUBMITTED",
            entity_type="undertaking_submission",
            entity_id=str(sub.id),
            actor_user_id=user.id,
            metadata={"undertaking_id": str(undertaking.id), "file_id": str(file_id)},
        )

        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def review_submission(
        cls,
        db: Session,
        submission_id: uuid.UUID,
        decision: str,
        review_comments: str,
        user: User,
    ) -> UndertakingSubmission:
        """
        Authorised dual-control verification of undertaking compliance evidence.
        Institution users are strictly forbidden from self-verifying submissions.
        """
        role_enum = normalize_role(user.role)
        if role_enum == UserRole.INSTITUTION_USER:
            raise ForbiddenError("Institution users cannot verify undertaking compliance submissions.")

        sub = db.get(UndertakingSubmission, submission_id)
        if not sub:
            raise NotFoundError("Submission not found.")

        undertaking = cls.get_undertaking(db, sub.undertaking_id, user)

        if not review_comments or not review_comments.strip():
            raise AppException("Review comments are mandatory.", code="COMMENTS_REQUIRED", status_code=422)

        now = datetime.now(timezone.utc)
        sub.reviewed_by_user_id = user.id
        sub.reviewed_at = now
        sub.review_comments = review_comments.strip()
        sub.review_status = decision

        if decision == "accepted":
            undertaking.status = "accepted"
            undertaking.verified_by_user_id = user.id
            undertaking.verified_at = now
            undertaking.verification_notes = review_comments.strip()
        elif decision == "rejected":
            undertaking.status = "rejected"
            undertaking.verified_by_user_id = user.id
            undertaking.verified_at = now
            undertaking.verification_notes = review_comments.strip()
        elif decision == "returned":
            undertaking.status = "returned"
            undertaking.verification_notes = review_comments.strip()
        else:
            raise AppException("Invalid review decision.", code="INVALID_DECISION", status_code=400)

        AuditService.record_action(
            db=db,
            action="UNDERTAKING_VERIFIED",
            entity_type="undertaking",
            entity_id=str(undertaking.id),
            actor_user_id=user.id,
            metadata={"decision": decision, "submission_id": str(sub.id), "notes": review_comments.strip()},
        )

        db.commit()
        db.refresh(sub)
        return sub
