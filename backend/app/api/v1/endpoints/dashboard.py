from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import Application, Document, EVC, Undertaking
from backend.app.schemas.common import DataResponse
from backend.app.schemas.dashboard import AgeingMetric, DashboardSummary, RegionalSummary

router = APIRouter()


@router.get("/summary", response_model=DataResponse[DashboardSummary], summary="Dashboard Summary Metrics")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Returns high-level application and pendency metrics.
    Demonstration data is clearly labeled.
    """
    try:
        total_apps = db.scalar(select(func.count(Application.id))) or 0
        in_progress = db.scalar(select(func.count(Application.id)).where(Application.status == "in_progress")) or 0
        pending_evc = db.scalar(select(func.count(EVC.id)).where(EVC.status.in_(["queued", "scheduled"]))) or 0
        pending_undertakings = db.scalar(select(func.count(Undertaking.id)).where(Undertaking.status == "pending")) or 0
    except Exception:
        # Fallback for empty/unmigrated DB during initial inspection
        total_apps = 12
        in_progress = 8
        pending_evc = 3
        pending_undertakings = 5

    return {
        "data": DashboardSummary(
            total_applications=total_apps,
            in_progress=in_progress,
            pending_scrutiny=max(0, in_progress - pending_evc),
            pending_evc=pending_evc,
            pending_undertakings=pending_undertakings,
            overdue_items=1,
            completed_this_cycle=2,
            is_demo_data=True,
        )
    }


@router.get("/ageing", response_model=DataResponse[List[AgeingMetric]], summary="Stage Ageing Distribution")
def get_stage_ageing():
    """
    Returns synthetic demonstration ageing distribution by stage.
    """
    return {
        "data": [
            AgeingMetric(stage_name="Scrutiny", under_7_days=5, between_7_14_days=2, over_14_days=1),
            AgeingMetric(stage_name="Re-Scrutiny", under_7_days=3, between_7_14_days=1, over_14_days=0),
            AgeingMetric(stage_name="EVC Scheduling", under_7_days=4, between_7_14_days=2, over_14_days=1),
            AgeingMetric(stage_name="EVC Report Review", under_7_days=2, between_7_14_days=1, over_14_days=0),
            AgeingMetric(stage_name="SAC / SHC", under_7_days=1, between_7_14_days=0, over_14_days=0),
        ]
    }
