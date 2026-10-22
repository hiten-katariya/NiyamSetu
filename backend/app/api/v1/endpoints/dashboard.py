from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.entities import Application, EVC, Institution, Undertaking, User
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.schemas.common import DataResponse
from backend.app.schemas.dashboard import AgeingMetric, DashboardSummary

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=DataResponse[DashboardSummary], summary="Dashboard Summary Metrics")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns scoped high-level application and pendency metrics.
    Demonstration data is clearly labeled.
    """
    role_enum = normalize_role(current_user.role)

    app_query = select(Application)
    evc_query = select(EVC)
    undertaking_query = select(Undertaking)

    # Apply institutional scoping
    if role_enum == UserRole.INSTITUTION_USER:
        inst_id = current_user.institution_id
        app_query = app_query.where(Application.institution_id == inst_id)
        evc_query = evc_query.join(Application).where(Application.institution_id == inst_id)
        undertaking_query = undertaking_query.where(Undertaking.assigned_institution_id == inst_id)

    elif role_enum == UserRole.REGIONAL_OFFICER:
        reg_id = current_user.region_id
        app_query = app_query.join(Application.institution).where(Institution.region_id == reg_id)
        evc_query = evc_query.where(EVC.assigned_region_id == reg_id)

    try:
        total_apps = db.scalar(select(func.count()).select_from(app_query.subquery())) or 0
        in_progress = (
            db.scalar(
                select(func.count()).select_from(
                    app_query.where(Application.status == "in_progress").subquery()
                )
            )
            or 0
        )
        pending_evc = (
            db.scalar(
                select(func.count()).select_from(
                    evc_query.where(EVC.status.in_(["queued", "scheduled"])).subquery()
                )
            )
            or 0
        )
        pending_undertakings = (
            db.scalar(
                select(func.count()).select_from(
                    undertaking_query.where(Undertaking.status == "pending").subquery()
                )
            )
            or 0
        )
    except Exception:
        total_apps = 1
        in_progress = 1
        pending_evc = 0
        pending_undertakings = 0

    return {
        "data": DashboardSummary(
            total_applications=total_apps,
            in_progress=in_progress,
            pending_scrutiny=max(0, in_progress - pending_evc),
            pending_evc=pending_evc,
            pending_undertakings=pending_undertakings,
            overdue_items=0,
            completed_this_cycle=0,
            is_demo_data=True,
        )
    }


@router.get("/ageing", response_model=DataResponse[List[AgeingMetric]], summary="Stage Ageing Distribution")
def get_stage_ageing(
    current_user: User = Depends(get_current_user),
):
    """
    Returns synthetic demonstration ageing distribution by stage for authorized users.
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
