from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.app.core.exceptions import AppException, ForbiddenError, NotFoundError
from backend.app.models.entities import (
    Application,
    EVC,
    EVCMember,
    EVCReport,
    Institution,
    Region,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.services.audit_service import AuditService


class EVCService:
    """
    Expert Visit Committee (EVC) Lifecycle & Workflow Service.
    Manages visits, scheduling, committee assignments, conduct tracking, and report reviews.
    """

    @classmethod
    def apply_evc_scoping(cls, stmt, user: User):
        """
        Applies server-side role and jurisdiction scoping to EVC queries.
        """
        role_enum = normalize_role(user.role)

        if role_enum in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.BUREAU_OFFICER, UserRole.SENIOR_AUTHORITY):
            return stmt

        if role_enum == UserRole.INSTITUTION_USER:
            if not user.institution_id:
                return stmt.where(EVC.id == None)  # Empty
            return stmt.join(EVC.application).where(Application.institution_id == user.institution_id)

        if role_enum == UserRole.REGIONAL_OFFICER:
            if not user.region_id:
                return stmt.where(EVC.id == None)
            return stmt.where(EVC.assigned_region_id == user.region_id)

        if role_enum == UserRole.COMMITTEE_MEMBER:
            # Strictly restricted to EVC visits where user is explicitly assigned as an active member
            return stmt.join(EVC.members).where(EVCMember.user_id == user.id)

        return stmt.where(EVC.id == None)

    @classmethod
    def get_evc(cls, db: Session, evc_id: uuid.UUID, user: User) -> EVC:
        """
        Retrieves a single EVC record with its members and reports, verifying access.
        """
        stmt = (
            select(EVC)
            .where(EVC.id == evc_id)
            .options(
                joinedload(EVC.application).joinedload(Application.institution),
                joinedload(EVC.assigned_region),
                joinedload(EVC.members).joinedload(EVCMember.user),
                joinedload(EVC.reports).joinedload(EVCReport.file),
                joinedload(EVC.reports).joinedload(EVCReport.submitted_by),
                joinedload(EVC.reports).joinedload(EVCReport.reviewed_by),
            )
        )
        stmt = cls.apply_evc_scoping(stmt, user)
        evc = db.scalars(stmt).unique().first()
        if not evc:
            raise NotFoundError("EVC record not found or inaccessible.")
        return evc

    @classmethod
    def create_evc(
        cls,
        db: Session,
        application_id: uuid.UUID,
        user: User,
        due_by: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> EVC:
        """
        Queues or creates a new EVC visit associated with an application.
        """
        role_enum = normalize_role(user.role)
        if role_enum not in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.REGIONAL_OFFICER, UserRole.SCRUTINY_OFFICER):
            raise ForbiddenError("Only authorized regional and administrative officers can queue an EVC.")

        app = db.get(Application, application_id)
        if not app:
            raise NotFoundError("Application not found.")

        # Check regional jurisdiction for regional officer
        if role_enum == UserRole.REGIONAL_OFFICER:
            inst = app.institution or db.get(Institution, app.institution_id)
            if inst and inst.region_id and inst.region_id != user.region_id:
                raise ForbiddenError("Cannot create EVC for an institution outside your regional jurisdiction.")

        inst = app.institution or db.get(Institution, app.institution_id)
        assigned_region_id = inst.region_id if inst else None

        evc = EVC(
            id=uuid.uuid4(),
            application_id=app.id,
            status="queued",
            due_by=due_by,
            assigned_region_id=assigned_region_id,
            notes=notes,
        )
        db.add(evc)

        AuditService.record_action(
            db=db,
            action="EVC_QUEUED",
            entity_type="evc",
            entity_id=str(evc.id),
            actor_user_id=user.id,
            metadata={"application_id": str(app.id), "due_by": due_by.isoformat() if due_by else None},
        )

        db.commit()
        db.refresh(evc)
        return evc

    @classmethod
    def schedule_evc(
        cls,
        db: Session,
        evc_id: uuid.UUID,
        user: User,
        scheduled_at: datetime,
        notes: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> EVC:
        """
        Schedules or reschedules an EVC visit.
        Mandates a change reason if modifying an existing schedule date.
        """
        role_enum = normalize_role(user.role)
        if role_enum not in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.REGIONAL_OFFICER):
            raise ForbiddenError("Only regional and administrative officers can schedule or reschedule an EVC.")

        evc = cls.get_evc(db, evc_id, user)

        if evc.status in ("conducted", "report_submitted", "review_complete", "cancelled"):
            raise AppException(
                f"Cannot reschedule an EVC with status '{evc.status}'.",
                code="INVALID_EVC_STATUS",
                status_code=400,
            )

        is_reschedule = evc.scheduled_at is not None
        if is_reschedule and (not reason or not reason.strip()):
            raise AppException(
                "A mandatory reason is required to reschedule an EVC visit.",
                code="REASON_REQUIRED",
                status_code=422,
            )

        previous_scheduled = evc.scheduled_at.isoformat() if evc.scheduled_at else None
        evc.scheduled_at = scheduled_at
        evc.status = "scheduled"
        if notes:
            evc.notes = f"{evc.notes}\n{notes}".strip() if evc.notes else notes

        action = "EVC_RESCHEDULED" if is_reschedule else "EVC_SCHEDULED"
        AuditService.record_action(
            db=db,
            action=action,
            entity_type="evc",
            entity_id=str(evc.id),
            actor_user_id=user.id,
            metadata={
                "previous_scheduled_at": previous_scheduled,
                "new_scheduled_at": scheduled_at.isoformat(),
                "reason": reason.strip() if reason else None,
            },
        )

        db.commit()
        db.refresh(evc)
        return evc

    @classmethod
    def assign_members(
        cls,
        db: Session,
        evc_id: uuid.UUID,
        user: User,
        members_data: List[Dict[str, Any]],
    ) -> EVC:
        """
        Assigns or updates committee members for an EVC visit.
        """
        role_enum = normalize_role(user.role)
        if role_enum not in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.REGIONAL_OFFICER):
            raise ForbiddenError("Only regional and administrative officers can assign committee members.")

        evc = cls.get_evc(db, evc_id, user)

        # Clear existing member records
        for m in list(evc.members):
            db.delete(m)

        new_members: List[EVCMember] = []
        for item in members_data:
            mem = EVCMember(
                id=uuid.uuid4(),
                evc_id=evc.id,
                user_id=item.get("user_id"),
                member_name=item["member_name"],
                member_role=item["member_role"],
            )
            db.add(mem)
            new_members.append(mem)

        AuditService.record_action(
            db=db,
            action="EVC_MEMBERS_ASSIGNED",
            entity_type="evc",
            entity_id=str(evc.id),
            actor_user_id=user.id,
            metadata={"assigned_count": len(new_members)},
        )

        db.commit()
        db.refresh(evc)
        return evc

    @classmethod
    def conduct_evc(
        cls,
        db: Session,
        evc_id: uuid.UUID,
        user: User,
        conducted_at: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> EVC:
        """
        Records the completion of the physical or virtual inspection visit.
        """
        role_enum = normalize_role(user.role)
        if role_enum not in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.REGIONAL_OFFICER, UserRole.COMMITTEE_MEMBER):
            raise ForbiddenError("Not authorized to record EVC conduct.")

        evc = cls.get_evc(db, evc_id, user)

        if evc.status not in ("scheduled", "queued"):
            raise AppException(f"Cannot mark EVC as conducted from status '{evc.status}'.", code="INVALID_STATUS", status_code=400)

        now = datetime.now(timezone.utc)
        evc.conducted_at = conducted_at or now
        evc.status = "conducted"
        # Set report SLA: default 7 calendar days from conduct
        evc.report_due_by = evc.conducted_at + timedelta(days=7)
        if notes:
            evc.notes = f"{evc.notes}\n[Conduct]: {notes}".strip() if evc.notes else notes

        AuditService.record_action(
            db=db,
            action="EVC_CONDUCTED",
            entity_type="evc",
            entity_id=str(evc.id),
            actor_user_id=user.id,
            metadata={"conducted_at": evc.conducted_at.isoformat(), "report_due_by": evc.report_due_by.isoformat()},
        )

        db.commit()
        db.refresh(evc)
        return evc

    @classmethod
    def submit_report(
        cls,
        db: Session,
        evc_id: uuid.UUID,
        user: User,
        file_id: uuid.UUID,
    ) -> EVCReport:
        """
        Registers an official EVC inspection report.
        """
        role_enum = normalize_role(user.role)
        if role_enum not in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.REGIONAL_OFFICER, UserRole.COMMITTEE_MEMBER):
            raise ForbiddenError("Not authorized to submit EVC inspection reports.")

        evc = cls.get_evc(db, evc_id, user)

        if evc.status not in ("conducted", "report_submitted", "queued", "scheduled"):
            raise AppException("EVC must be scheduled or conducted before submitting a report.", code="INVALID_STATUS", status_code=400)

        now = datetime.now(timezone.utc)
        report = EVCReport(
            id=uuid.uuid4(),
            evc_id=evc.id,
            file_id=file_id,
            submitted_by_user_id=user.id,
            submitted_at=now,
            review_status="pending_review",
        )
        db.add(report)

        evc.status = "report_submitted"
        evc.report_submitted_at = now

        AuditService.record_action(
            db=db,
            action="EVC_REPORT_SUBMITTED",
            entity_type="evc_report",
            entity_id=str(report.id),
            actor_user_id=user.id,
            metadata={"evc_id": str(evc.id), "file_id": str(file_id)},
        )

        db.commit()
        db.refresh(report)
        return report

    @classmethod
    def review_report(
        cls,
        db: Session,
        report_id: uuid.UUID,
        user: User,
        decision: str,
        review_comments: str,
    ) -> EVCReport:
        """
        Authorised supervisory review of an EVC report.
        Allows acceptance or return for corrections with mandatory comments.
        """
        role_enum = normalize_role(user.role)
        if role_enum not in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.REGIONAL_OFFICER, UserRole.SENIOR_AUTHORITY):
            raise ForbiddenError("Only authorized regional and senior authorities can review EVC reports.")

        report = db.get(EVCReport, report_id)
        if not report:
            raise NotFoundError("EVC report not found.")

        evc = cls.get_evc(db, report.evc_id, user)

        now = datetime.now(timezone.utc)
        report.reviewed_by_user_id = user.id
        report.reviewed_at = now
        report.review_comments = review_comments.strip()

        if decision == "accepted":
            report.review_status = "accepted"
            evc.status = "review_complete"
        elif decision == "returned_for_correction":
            report.review_status = "returned_for_correction"
            evc.status = "conducted"  # Needs revised report
        else:
            raise AppException("Invalid review decision.", code="INVALID_DECISION", status_code=400)

        AuditService.record_action(
            db=db,
            action="EVC_REPORT_REVIEWED",
            entity_type="evc_report",
            entity_id=str(report.id),
            actor_user_id=user.id,
            metadata={"decision": decision, "comments": review_comments.strip()},
        )

        db.commit()
        db.refresh(report)
        return report
