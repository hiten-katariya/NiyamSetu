from typing import Dict, List
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
