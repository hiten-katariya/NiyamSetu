import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
#SYBERSURFERS
from backend.app.db.session import SessionLocal
from backend.app.models.entities import (
    Application,
    Document,
    Notification,
    ReminderRule,
    SchedulerRun,
    Undertaking,
    User,
)
from backend.app.services.escalation_service import EscalationService
from backend.app.services.reminder_service import ReminderService

logger = logging.getLogger("niyamsetu.worker.deadline_scan")


def execute_deadline_scan(
    db: Optional[Session] = None,
    as_of_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Executes a unified deadline, reminder, escalation, and compliance scan.
    Evaluates applications, undertakings, and document validity.
    Records execution metrics in `scheduler_runs` and guarantees idempotent processing.
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True

    now = as_of_time or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    today = now.date()

    # 1. Initialize SchedulerRun record
    run_record = SchedulerRun(
        id=uuid.uuid4(),
        job_name="deadline_scan",
        started_at=now,
        status="running",
        items_scanned=0,
        items_processed=0,
    )
    db.add(run_record)
    db.commit()

    items_scanned = 0
    reminders_created = 0
    escalations_created = 0

    try:
        # 2. Query active applications
        stmt = (
            select(Application)
            .where(Application.status.in_(["in_progress", "returned"]))
            .options(
                joinedload(Application.institution),
                joinedload(Application.current_stage),
            )
        )
        applications = list(db.scalars(stmt).all())
        items_scanned += len(applications)

        # 3. Process application reminders and escalations
        for app in applications:
            new_notifs = ReminderService.process_application_reminders(db, app, as_of_time=now)
            reminders_created += len(new_notifs)

            new_escs = EscalationService.process_application_escalations(db, app, as_of_time=now)
            escalations_created += len(new_escs)

        # 4. Scan Undertaking deadlines & mark overdue
        undertakings = list(
            db.scalars(
                select(Undertaking).where(Undertaking.status.in_(["pending", "returned"]))
            ).all()
        )
        items_scanned += len(undertakings)

        for u in undertakings:
            if u.due_date < today:
                u.status = "overdue"

            # Check reminder rules for undertakings
            rules = list(
                db.scalars(
                    select(ReminderRule).where(
                        ReminderRule.target_type == "undertaking",
                        ReminderRule.is_active == True,
                    )
                ).all()
            )
            days_left = (u.due_date - today).days
            for rule in rules:
                if days_left <= rule.days_before_due and days_left >= 0:
                    # Find recipient users in the assigned institution
                    inst_users = list(
                        db.scalars(
                            select(User).where(
                                User.institution_id == u.assigned_institution_id,
                                User.is_active == True,
                            )
                        ).all()
                    )
                    for user in inst_users:
                        dedupe_key = f"rem:undertaking:{u.id}:{rule.id}:{days_left}:u:{user.id}"
                        existing = db.scalar(select(Notification.id).where(Notification.dedupe_key == dedupe_key))
                        if not existing:
                            notif = Notification(
                                id=uuid.uuid4(),
                                recipient_user_id=user.id,
                                application_id=u.application_id,
                                target_type="undertaking",
                                target_id=u.id,
                                channel="in_app",
                                title=f"Undertaking Due Soon: {u.title}",
                                body=f"Undertaking '{u.title}' is due on {u.due_date.isoformat()} ({days_left} days remaining).",
                                status="unread",
                                dedupe_key=dedupe_key,
                                sent_at=now,
                            )
                            db.add(notif)
                            reminders_created += 1

        # 5. Scan expiring/expired documents
        docs = list(
            db.scalars(
                select(Document).where(Document.valid_to != None)  # noqa: E711
            ).all()
        )
        items_scanned += len(docs)

        for doc in docs:
            if doc.valid_to and doc.valid_to < today and doc.verification_status != "expired":
                doc.verification_status = "expired"

        db.commit()

        # 6. Finalize SchedulerRun
        finished_at = datetime.now(timezone.utc)
        run_record.status = "success"
        run_record.finished_at = finished_at
        run_record.items_scanned = items_scanned
        run_record.items_processed = reminders_created + escalations_created
        db.commit()

        logger.info(
            f"Deadline scan completed successfully. Scanned: {items_scanned}, "
            f"Reminders: {reminders_created}, Escalations: {escalations_created}"
        )

        return {
            "status": "success",
            "run_id": str(run_record.id),
            "items_scanned": items_scanned,
            "reminders_created": reminders_created,
            "escalations_created": escalations_created,
            "items_processed": run_record.items_processed,
            "started_at": run_record.started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
        }

    except Exception as exc:
        db.rollback()
        finished_at = datetime.now(timezone.utc)
        run_record.status = "failed"
        run_record.finished_at = finished_at
        run_record.error_summary = str(exc)
        try:
            db.commit()
        except Exception:
            pass
        logger.error(f"Deadline scan failed: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
            "started_at": run_record.started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
        }

    finally:
        if should_close_db:
            db.close()
