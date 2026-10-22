from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel
from backend.app.schemas.common import BaseSchema


class SchedulerRunItem(BaseSchema):
    id: uuid.UUID
    job_name: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    items_scanned: int
    items_processed: int
    duration_seconds: Optional[float] = None
    error_summary: Optional[str] = None


class WorkerMonitoringResponse(BaseModel):
    status: str  # operational, stale, warning, failed, never_run
    last_run: Optional[SchedulerRunItem] = None
    last_successful_run: Optional[SchedulerRunItem] = None
    latest_failed_run: Optional[SchedulerRunItem] = None
    recent_runs: List[SchedulerRunItem]
    total_runs: int
    success_runs: int
    failed_runs: int


class NotificationMonitoringResponse(BaseModel):
    unread_count: int
    read_count: int
    acknowledged_count: int
    total_count: int
