import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import SessionLocal
from backend.app.models.entities import Application, SchedulerRun
from backend.app.services.escalation_service import EscalationService
from backend.app.services.reminder_service import ReminderService

logger = logging.getLogger("niyamsetu.worker.deadline_scan")


def execute_deadline_scan(
    db: Optional[Session] = None,
    as_of_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Executes a comprehensive deadline, reminder, and escalation scan.
    Records execution metrics in `scheduler_runs` and guarantees idempotent processing.
    Can be run synchronously in unit tests, via CLI (`--once`), or via APScheduler worker.
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True

    now = as_of_time or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

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
        items_scanned = len(applications)

        # 3. Process reminders and escalations
        for app in applications:
            new_notifs = ReminderService.process_application_reminders(db, app, as_of_time=now)
            reminders_created += len(new_notifs)

            new_escs = EscalationService.process_application_escalations(db, app, as_of_time=now)
            escalations_created += len(new_escs)

        db.commit()

        # 4. Finalize SchedulerRun
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
        run_record.items_scanned = items_scanned
        run_record.items_processed = reminders_created + escalations_created
        run_record.error_summary = str(exc)
        try:
            db.commit()
        except Exception:
            pass

        logger.error(f"Deadline scan failed: {exc}", exc_info=True)
        return {
            "status": "failed",
            "run_id": str(run_record.id),
            "items_scanned": items_scanned,
            "error": str(exc),
        }

    finally:
        if should_close_db:
            db.close()
