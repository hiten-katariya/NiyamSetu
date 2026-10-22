from datetime import datetime, timezone
from typing import List, Optional, Set
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.core.exceptions import AppException, ForbiddenError, NotFoundError
from backend.app.models.entities import (
    Application,
    Escalation,
    EscalationRule,
    Institution,
    Notification,
    RouteStage,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.services.audit_service import AuditService
from backend.app.services.deadline_service import DeadlineService


class EscalationService:
    """
    Overdue Escalation Engine.
    Detects breached stage SLAs, triggers multi-tier escalations idempotently,
    and dispatches high-priority alerts to authorized supervisory desks.
    """

    @classmethod
    def resolve_recipients_for_escalation(
        cls,
        db: Session,
        application: Application,
        target_roles: List[str],
    ) -> List[User]:
        """
        Resolves supervisory officers authorized to receive escalation alerts.
        """
        inst = application.institution or db.get(Institution, application.institution_id)
        region_id = inst.region_id if inst else None

        recipients: List[User] = []
        seen_user_ids: Set[uuid.UUID] = set()

        for role_str in target_roles:
            stmt = select(User).where(User.is_active == True)  # noqa: E712

            if role_str == UserRole.REGIONAL_OFFICER.value:
                if region_id:
                    stmt = stmt.where(User.role == role_str, User.region_id == region_id)
                else:
                    stmt = stmt.where(User.role == role_str)
            else:
                stmt = stmt.where(User.role == role_str)

            matched_users = list(db.scalars(stmt).all())
            for u in matched_users:
                if u.id not in seen_user_ids:
                    seen_user_ids.add(u.id)
                    recipients.append(u)

        return recipients

    @classmethod
    def process_application_escalations(
        cls,
        db: Session,
        application: Application,
        as_of_time: Optional[datetime] = None,
    ) -> List[Escalation]:
        """
        Evaluates overdue status against active escalation rules and creates
        deduplicated escalation records and notifications.
        """
        now = as_of_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        deadline_res = DeadlineService.calculate_application_deadline(
            db=db,
            application=application,
            as_of_time=now,
        )

        if not deadline_res.due_date or not deadline_res.is_overdue:
            return []

        days_overdue = (now - deadline_res.due_date).total_seconds() / 86400.0

        rules_stmt = (
            select(EscalationRule)
            .where(
                EscalationRule.target_type == "application",
                EscalationRule.is_active == True,  # noqa: E712
            )
            .order_by(EscalationRule.level.asc())
        )
        rules = list(db.scalars(rules_stmt).all())

        new_escalations: List[Escalation] = []
        stage = application.current_stage
        if not stage or stage.id != application.current_stage_id:
            stage = db.get(RouteStage, application.current_stage_id)
        stage_name = stage.stage_name if stage else "Current Stage"
        inst = application.institution or db.get(Institution, application.institution_id)
        inst_name = inst.name if inst else "Institution"

        for rule in rules:
            if days_overdue >= rule.days_after_due:
                # Check idempotency: does an open escalation already exist for this application and level?
                existing_esc_stmt = select(Escalation).where(
                    Escalation.application_id == application.id,
                    Escalation.level == rule.level,
                    Escalation.status == "open",
                )
                if db.scalar(existing_esc_stmt):
                    continue

                recipients = cls.resolve_recipients_for_escalation(
                    db=db,
                    application=application,
                    target_roles=rule.recipient_roles,
                )

                assigned_to_user_id = recipients[0].id if recipients else None

                esc = Escalation(
                    id=uuid.uuid4(),
                    application_id=application.id,
                    target_type="application",
                    target_id=application.id,
                    level=rule.level,
                    assigned_to_user_id=assigned_to_user_id,
                    status="open",
                    triggered_at=now,
                )
                db.add(esc)
                new_escalations.append(esc)

                # Dispatch notifications to all resolved supervisory recipients
                deadline_date_str = deadline_res.due_date.date().isoformat()
                for recipient in recipients:
                    dedupe_key = f"esc:app:{application.id}:{rule.level}:{deadline_date_str}:u:{recipient.id}"
                    existing_notif = db.scalar(select(Notification.id).where(Notification.dedupe_key == dedupe_key))
                    if existing_notif:
                        continue

                    title = f"ESCALATION Level {rule.level}: Application {application.reference_no} Overdue"
                    body = (
                        f"CRITICAL SLA BREACH: Application {application.reference_no} ({inst_name}) is "
                        f"{int(days_overdue)} day(s) overdue for stage '{stage_name}'. "
                        f"Escalated to Tier {rule.level} for urgent administrative intervention."
                    )

                    notif = Notification(
                        id=uuid.uuid4(),
                        recipient_user_id=recipient.id,
                        application_id=application.id,
                        target_type="application",
                        target_id=application.id,
                        channel="in_app",
                        title=title,
                        body=body,
                        status="unread",
                        dedupe_key=dedupe_key,
                        sent_at=now,
                    )
                    db.add(notif)

                # Record tamper-evident audit event
                AuditService.record_action(
                    db=db,
                    action="APPLICATION_ESCALATED",
                    entity_type="application",
                    entity_id=str(application.id),
                    actor_user_id=assigned_to_user_id or application.id,
                    metadata={
                        "reference_no": application.reference_no,
                        "escalation_level": rule.level,
                        "days_overdue": round(days_overdue, 1),
                        "due_date": deadline_res.due_date.isoformat(),
                    },
                )

        return new_escalations

    @classmethod
    def scan_all_escalations(
        cls,
        db: Session,
        as_of_time: Optional[datetime] = None,
    ) -> int:
        """
        Scans all active applications and creates necessary tiered escalations.
        """
        stmt = (
            select(Application)
            .where(Application.status.in_(["in_progress", "returned"]))
            .options(
                joinedload(Application.institution),
                joinedload(Application.current_stage),
            )
        )
        apps = list(db.scalars(stmt).all())
        total_created = 0

        for app in apps:
            escs = cls.process_application_escalations(db, app, as_of_time)
            total_created += len(escs)

        if total_created > 0:
            db.commit()

        return total_created

    @classmethod
    def resolve_escalation(
        cls,
        db: Session,
        escalation_id: uuid.UUID,
        user: User,
        resolution_notes: str,
    ) -> Escalation:
        """
        Resolves an active escalation with mandatory review notes and role verification.
        """
        if not resolution_notes or not resolution_notes.strip():
            raise AppException("Resolution notes are required to resolve an escalation.", code="NOTES_REQUIRED", status_code=422)

        role_enum = normalize_role(user.role)
        if role_enum == UserRole.INSTITUTION_USER:
            raise ForbiddenError("Institution users cannot resolve statutory escalations.")

        esc = db.get(Escalation, escalation_id)
        if not esc:
            raise NotFoundError("Escalation not found.")

        # Scoping verification: Regional officers can only resolve escalations for their region
        if role_enum == UserRole.REGIONAL_OFFICER:
            app = esc.application or (db.get(Application, esc.application_id) if esc.application_id else None)
            if app:
                inst = app.institution or db.get(Institution, app.institution_id)
                if inst and inst.region_id and inst.region_id != user.region_id:
                    raise ForbiddenError("Cannot resolve escalations belonging to another administrative region.")

        now = datetime.now(timezone.utc)
        esc.status = "resolved"
        esc.resolved_at = now
        esc.resolution_notes = resolution_notes.strip()

        AuditService.record_action(
            db=db,
            action="ESCALATION_RESOLVED",
            entity_type="escalation",
            entity_id=str(esc.id),
            actor_user_id=user.id,
            metadata={
                "application_id": str(esc.application_id) if esc.application_id else None,
                "escalation_level": esc.level,
                "resolution_notes": esc.resolution_notes,
            },
        )

        db.commit()
        db.refresh(esc)
        return esc
