from datetime import datetime, timezone
from typing import List, Optional, Set
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.models.entities import (
    Application,
    Institution,
    Notification,
    ReminderRule,
    RouteStage,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.services.deadline_service import DeadlineService


class ReminderService:
    """
    Automated Reminder Engine.
    Evaluates approaching deadlines against configurable reminder rules
    and generates in-app notifications idempotently.
    """

    @classmethod
    def resolve_recipients_for_application(
        cls,
        db: Session,
        application: Application,
        target_roles: List[str],
    ) -> List[User]:
        """
        Resolves active users authorized to receive notifications for this application,
        strictly respecting institutional boundaries, regional scopes, and desk assignments.
        """
        inst = application.institution or db.get(Institution, application.institution_id)
        region_id = inst.region_id if inst else None

        recipients: List[User] = []
        seen_user_ids: Set[uuid.UUID] = set()

        for role_str in target_roles:
            stmt = select(User).where(User.is_active == True)  # noqa: E712

            if role_str == UserRole.INSTITUTION_USER.value:
                # Strictly restricted to users belonging to the applicant institution
                stmt = stmt.where(User.role == role_str, User.institution_id == application.institution_id)

            elif role_str == UserRole.REGIONAL_OFFICER.value:
                # Strictly restricted to Regional Officers of the matching region
                if region_id:
                    stmt = stmt.where(User.role == role_str, User.region_id == region_id)
                else:
                    stmt = stmt.where(User.role == role_str)

            elif role_str == UserRole.SCRUTINY_OFFICER.value:
                if application.assigned_to_user_id:
                    stmt = stmt.where(User.id == application.assigned_to_user_id)
                else:
                    stmt = stmt.where(User.role == role_str)

            else:
                # Senior authorities, bureau officers, system admins
                stmt = stmt.where(User.role == role_str)

            matched_users = list(db.scalars(stmt).all())
            for u in matched_users:
                if u.id not in seen_user_ids:
                    seen_user_ids.add(u.id)
                    recipients.append(u)

        return recipients

    @classmethod
    def process_application_reminders(
        cls,
        db: Session,
        application: Application,
        as_of_time: Optional[datetime] = None,
    ) -> List[Notification]:
        """
        Evaluates active reminder rules for a single application and creates
        deduplicated in-app notifications.
        """
        now = as_of_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        deadline_res = DeadlineService.calculate_application_deadline(
            db=db,
            application=application,
            as_of_time=now,
        )

        if not deadline_res.due_date or deadline_res.is_overdue:
            return []

        days_remaining = deadline_res.days_remaining or 0.0

        rules_stmt = select(ReminderRule).where(
            ReminderRule.target_type == "application",
            ReminderRule.is_active == True,  # noqa: E712
        )
        rules = list(db.scalars(rules_stmt).all())

        new_notifications: List[Notification] = []

        stage = application.current_stage
        if not stage or stage.id != application.current_stage_id:
            stage = db.get(RouteStage, application.current_stage_id)
        stage_name = stage.stage_name if stage else "Review"
        inst = application.institution or db.get(Institution, application.institution_id)
        inst_name = inst.name if inst else "Institution"

        for rule in rules:
            if days_remaining <= rule.days_before_due:
                # Rule triggered! Resolve authorized recipients
                recipients = cls.resolve_recipients_for_application(
                    db=db,
                    application=application,
                    target_roles=rule.recipient_roles,
                )

                for recipient in recipients:
                    # Deduplication key includes application, stage, rule, offset, target deadline, and recipient
                    deadline_date_str = deadline_res.due_date.date().isoformat()
                    dedupe_key = (
                        f"rem:app:{application.id}:{application.current_stage_id}:"
                        f"{rule.id}:{rule.days_before_due}:{deadline_date_str}:u:{recipient.id}"
                    )

                    # Check idempotency
                    existing = db.scalar(select(Notification.id).where(Notification.dedupe_key == dedupe_key))
                    if existing:
                        continue

                    title = f"Reminder: {application.reference_no} SLA Deadline Approaching"
                    remaining_display = max(0, int(days_remaining))
                    body = (
                        f"Application {application.reference_no} ({inst_name}) is due in {remaining_display} day(s) "
                        f"for stage '{stage_name}'. Deadline: {deadline_res.due_date.strftime('%Y-%m-%d %H:%M UTC')}."
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
                    new_notifications.append(notif)

        return new_notifications

    @classmethod
    def scan_all_reminders(
        cls,
        db: Session,
        as_of_time: Optional[datetime] = None,
    ) -> int:
        """
        Scans all active applications and creates due reminders.
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
            notifs = cls.process_application_reminders(db, app, as_of_time)
            total_created += len(notifs)

        if total_created > 0:
            db.commit()

        return total_created
