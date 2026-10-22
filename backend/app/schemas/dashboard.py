from datetime import datetime
from typing import Dict, List, Optional
import uuid
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_applications: int
    in_progress: int
    pending_scrutiny: int
    pending_evc: int
    pending_undertakings: int
    overdue_items: int
    completed_this_cycle: int
    is_demo_data: bool = True


class AgeingMetric(BaseModel):
    stage_name: str
    under_7_days: int
    between_7_14_days: int
    over_14_days: int


class RegionalSummary(BaseModel):
    region_code: str
    region_name: str
    total_applications: int
    pending_count: int
    evc_due_count: int
    overdue_count: int


class PendencyMetrics(BaseModel):
    total_pending: int
    by_stage: Dict[str, int]
    by_region: Dict[str, int]
    overdue_count: int
    on_hold_count: int
    due_soon_count: int


class AttentionItemResponse(BaseModel):
    id: uuid.UUID
    application_number: str
    institution_name: str
    current_stage_name: str
    status: str  # overdue, due_soon, on_hold, returned
    reason: str
    days_in_stage: int
    due_date: Optional[datetime] = None
    priority: str  # critical, high, medium, normal
