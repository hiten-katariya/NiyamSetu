from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.db.session import get_db
from backend.app.models.entities import Notification, SchedulerRun, User
from backend.app.permissions.roles import UserRole
from backend.app.schemas.common import DataResponse
from backend.app.schemas.monitoring import (
    NotificationMonitoringResponse,
    SchedulerRunItem,
    WorkerMonitoringResponse,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/worker", response_model=DataResponse[WorkerMonitoringResponse], summary="Worker Operational Health")
def get_worker_monitoring(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns background worker execution history, scan performance, and diagnostic statuses.
    """
    recent_runs_stmt = select(SchedulerRun).order_by(SchedulerRun.started_at.desc()).limit(15)
    recent_runs_raw = list(db.scalars(recent_runs_stmt).all())

    total_runs = db.scalar(select(func.count(SchedulerRun.id))) or 0
    success_runs = db.scalar(select(func.count(SchedulerRun.id)).where(SchedulerRun.status == "success")) or 0
    failed_runs = db.scalar(select(func.count(SchedulerRun.id)).where(SchedulerRun.status == "failed")) or 0

    last_successful_stmt = (
        select(SchedulerRun)
        .where(SchedulerRun.status == "success")
        .order_by(SchedulerRun.started_at.desc())
        .limit(1)
    )
    last_success_raw = db.scalars(last_successful_stmt).first()

    latest_failed_stmt = (
        select(SchedulerRun)
        .where(SchedulerRun.status == "failed")
        .order_by(SchedulerRun.started_at.desc())
        .limit(1)
    )
    latest_failed_raw = db.scalars(latest_failed_stmt).first()

    def format_run_item(r: Optional[SchedulerRun]) -> Optional[SchedulerRunItem]:
        if not r:
            return None
        dur = None
        if r.started_at and r.finished_at:
            dur = round((r.finished_at - r.started_at).total_seconds(), 2)
        return SchedulerRunItem(
            id=r.id,
            job_name=r.job_name,
            started_at=r.started_at,
            finished_at=r.finished_at,
            status=r.status,
            items_scanned=r.items_scanned or 0,
            items_processed=r.items_processed or 0,
            duration_seconds=dur,
            error_summary=r.error_summary,
        )

    recent_items = [format_run_item(r) for r in recent_runs_raw if r is not None]
    last_run_item = recent_items[0] if recent_items else None

    # Status classification
    now = datetime.now(timezone.utc)
    status = "never_run"
    if last_run_item:
        run_time = last_run_item.started_at
        if run_time.tzinfo is None:
            run_time = run_time.replace(tzinfo=timezone.utc)

        if last_run_item.status == "failed":
            status = "failed"
        elif (now - run_time).total_seconds() > 7200:  # > 2 hours
            status = "stale"
        elif last_run_item.status == "running":
            status = "running"
        else:
            status = "operational"

    return {
        "data": WorkerMonitoringResponse(
            status=status,
            last_run=last_run_item,
            last_successful_run=format_run_item(last_success_raw),
            latest_failed_run=format_run_item(latest_failed_raw),
            recent_runs=recent_items,
            total_runs=total_runs,
            success_runs=success_runs,
            failed_runs=failed_runs,
        )
    }


@router.get("/notifications", response_model=DataResponse[NotificationMonitoringResponse], summary="Notification Processing Metrics")
def get_notification_monitoring(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns notification processing metrics and queue states.
    """
    unread = db.scalar(select(func.count(Notification.id)).where(Notification.status == "unread")) or 0
    read = db.scalar(select(func.count(Notification.id)).where(Notification.status == "read")) or 0
    ack = db.scalar(select(func.count(Notification.id)).where(Notification.status == "acknowledged")) or 0
    total = unread + read + ack

    return {
        "data": NotificationMonitoringResponse(
            unread_count=unread,
            read_count=read,
            acknowledged_count=ack,
            total_count=total,
        )
    }
