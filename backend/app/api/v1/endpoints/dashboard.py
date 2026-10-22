from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.entities import (
    Application,
    EVC,
    Institution,
    Region,
    RouteStage,
    Undertaking,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.schemas.common import DataResponse
from backend.app.schemas.dashboard import (
    AgeingMetric,
    AttentionItemResponse,
    DashboardSummary,
    PendencyMetrics,
)
from backend.app.services.deadline_service import DeadlineService

router = APIRouter(dependencies=[Depends(get_current_user)])


def get_scoped_applications_query(user: User):
    """
    Constructs a base application query with proper role and regional scoping applied.
    """
    role_enum = normalize_role(user.role)
    stmt = (
        select(Application)
        .options(
            joinedload(Application.institution),
            joinedload(Application.current_stage),
        )
    )

    if role_enum == UserRole.INSTITUTION_USER:
        if not user.institution_id:
            return stmt.where(Application.id == None)  # Return empty
        stmt = stmt.where(Application.institution_id == user.institution_id)

    elif role_enum == UserRole.REGIONAL_OFFICER:
        if not user.region_id:
            return stmt.where(Application.id == None)
        stmt = stmt.join(Application.institution).where(Institution.region_id == user.region_id)

    return stmt


@router.get("/summary", response_model=DataResponse[DashboardSummary], summary="Dashboard Summary Metrics")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns scoped high-level application, pendency, and SLA compliance metrics.
    """
    role_enum = normalize_role(current_user.role)

    app_query = select(Application)
    evc_query = select(EVC)
    undertaking_query = select(Undertaking)

    if role_enum == UserRole.INSTITUTION_USER:
        inst_id = current_user.institution_id
        app_query = app_query.where(Application.institution_id == inst_id)
        evc_query = evc_query.join(Application).where(Application.institution_id == inst_id)
        undertaking_query = undertaking_query.where(Undertaking.assigned_institution_id == inst_id)

    elif role_enum == UserRole.REGIONAL_OFFICER:
        reg_id = current_user.region_id
        app_query = app_query.join(Application.institution).where(Institution.region_id == reg_id)
        evc_query = evc_query.where(EVC.assigned_region_id == reg_id)

    total_apps = db.scalar(select(func.count()).select_from(app_query.subquery())) or 0
    in_progress = (
        db.scalar(
            select(func.count()).select_from(
                app_query.where(Application.status.in_(["in_progress", "submitted"])).subquery()
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
    completed_apps = (
        db.scalar(
            select(func.count()).select_from(
                app_query.where(Application.status == "completed").subquery()
            )
        )
        or 0
    )

    # Calculate real overdue items via DeadlineService
    active_apps_stmt = get_scoped_applications_query(current_user).where(
        Application.status.in_(["in_progress", "returned"])
    )
    active_apps = list(db.scalars(active_apps_stmt).all())
    now = datetime.now(timezone.utc)

    overdue_count = 0
    for app in active_apps:
        res = DeadlineService.calculate_application_deadline(db, app, as_of_time=now)
        if res.is_overdue:
            overdue_count += 1

    return {
        "data": DashboardSummary(
            total_applications=total_apps,
            in_progress=in_progress,
            pending_scrutiny=max(0, in_progress - pending_evc),
            pending_evc=pending_evc,
            pending_undertakings=pending_undertakings,
            overdue_items=overdue_count,
            completed_this_cycle=completed_apps,
            is_demo_data=False,
        )
    }


@router.get("/ageing", response_model=DataResponse[List[AgeingMetric]], summary="Stage Ageing Distribution")
def get_stage_ageing(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns real stage ageing distribution calculated by the Deadline Engine for active applications.
    """
    active_apps_stmt = get_scoped_applications_query(current_user).where(
        Application.status.in_(["in_progress", "returned"])
    )
    active_apps = list(db.scalars(active_apps_stmt).all())
    now = datetime.now(timezone.utc)

    # Aggregators by stage name
    stage_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"under_7": 0, "7_to_14": 0, "over_14": 0})

    for app in active_apps:
        stage_name = app.current_stage.stage_name if app.current_stage else "Pending Stage"
        res = DeadlineService.calculate_application_deadline(db, app, as_of_time=now)
        ageing = res.ageing_days

        if ageing < 7.0:
            stage_counts[stage_name]["under_7"] += 1
        elif ageing <= 14.0:
            stage_counts[stage_name]["7_to_14"] += 1
        else:
            stage_counts[stage_name]["over_14"] += 1

    # If no active applications exist, provide fallback baseline stages for chart rendering
    if not stage_counts:
        return {
            "data": [
                AgeingMetric(stage_name="Scrutiny", under_7_days=0, between_7_14_days=0, over_14_days=0),
                AgeingMetric(stage_name="Re-Scrutiny", under_7_days=0, between_7_14_days=0, over_14_days=0),
                AgeingMetric(stage_name="EVC Scheduling", under_7_days=0, between_7_14_days=0, over_14_days=0),
            ]
        }

    metrics = [
        AgeingMetric(
            stage_name=s_name,
            under_7_days=data["under_7"],
            between_7_14_days=data["7_to_14"],
            over_14_days=data["over_14"],
        )
        for s_name, data in sorted(stage_counts.items())
    ]
    return {"data": metrics}


@router.get("/pendency", response_model=DataResponse[PendencyMetrics], summary="Pendency Breakdown")
def get_pendency_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns detailed pendency analytics aggregated by stage, region, and SLA urgency.
    """
    active_apps_stmt = get_scoped_applications_query(current_user).where(
        Application.status.in_(["in_progress", "returned", "on_hold"])
    )
    active_apps = list(db.scalars(active_apps_stmt).all())
    now = datetime.now(timezone.utc)

    by_stage: Dict[str, int] = defaultdict(int)
    by_region: Dict[str, int] = defaultdict(int)
    overdue_count = 0
    on_hold_count = 0
    due_soon_count = 0

    # Cache region names
    regions_map = {r.id: r.name for r in db.scalars(select(Region)).all()}

    for app in active_apps:
        stage_name = app.current_stage.stage_name if app.current_stage else "Unassigned"
        by_stage[stage_name] += 1

        reg_name = "Unassigned"
        if app.institution and app.institution.region_id:
            reg_name = regions_map.get(app.institution.region_id, "Unknown Region")
        by_region[reg_name] += 1

        if app.status == "on_hold":
            on_hold_count += 1

        res = DeadlineService.calculate_application_deadline(db, app, as_of_time=now)
        if res.is_overdue:
            overdue_count += 1
        elif res.is_due_soon:
            due_soon_count += 1

    return {
        "data": PendencyMetrics(
            total_pending=len(active_apps),
            by_stage=dict(by_stage),
            by_region=dict(by_region),
            overdue_count=overdue_count,
            on_hold_count=on_hold_count,
            due_soon_count=due_soon_count,
        )
    }


@router.get("/attention", response_model=DataResponse[List[AttentionItemResponse]], summary="Items Requiring Immediate Attention")
def get_attention_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns priority-ranked items requiring human intervention:
    1. Critical: Overdue applications (breached stage SLA)
    2. High: Approaching deadline within threshold (due soon)
    3. Medium: Applications on administrative hold
    4. Normal: Applications returned for clarification
    """
    active_apps_stmt = get_scoped_applications_query(current_user).where(
        Application.status.in_(["in_progress", "returned", "on_hold"])
    )
    active_apps = list(db.scalars(active_apps_stmt).all())
    now = datetime.now(timezone.utc)

    items: List[AttentionItemResponse] = []

    for app in active_apps:
        res = DeadlineService.calculate_application_deadline(db, app, as_of_time=now)
        inst_name = app.institution.name if app.institution else "Unknown Institution"
        stage_name = app.current_stage.stage_name if app.current_stage else "Unassigned Stage"
        ageing_days = int(res.ageing_days)

        if res.is_overdue:
            days_over = abs(res.days_remaining) if res.days_remaining is not None else 0
            items.append(
                AttentionItemResponse(
                    id=app.id,
                    application_number=app.reference_no,
                    institution_name=inst_name,
                    current_stage_name=stage_name,
                    status="overdue",
                    reason=f"SLA breached by {days_over:.1f} days",
                    days_in_stage=ageing_days,
                    due_date=res.due_date,
                    priority="critical",
                )
            )
        elif res.is_due_soon:
            days_left = res.days_remaining if res.days_remaining is not None else 0
            items.append(
                AttentionItemResponse(
                    id=app.id,
                    application_number=app.reference_no,
                    institution_name=inst_name,
                    current_stage_name=stage_name,
                    status="due_soon",
                    reason=f"Due in {days_left:.1f} days",
                    days_in_stage=ageing_days,
                    due_date=res.due_date,
                    priority="high",
                )
            )
        elif app.status == "on_hold":
            items.append(
                AttentionItemResponse(
                    id=app.id,
                    application_number=app.reference_no,
                    institution_name=inst_name,
                    current_stage_name=stage_name,
                    status="on_hold",
                    reason="Application paused on administrative hold",
                    days_in_stage=ageing_days,
                    due_date=res.due_date,
                    priority="medium",
                )
            )
        elif app.status == "returned":
            items.append(
                AttentionItemResponse(
                    id=app.id,
                    application_number=app.reference_no,
                    institution_name=inst_name,
                    current_stage_name=stage_name,
                    status="returned",
                    reason="Returned for institutional clarification",
                    days_in_stage=ageing_days,
                    due_date=res.due_date,
                    priority="medium",
                )
            )

    priority_order = {"critical": 0, "high": 1, "medium": 2, "normal": 3}
    items.sort(key=lambda x: (priority_order.get(x.priority, 99), -(x.days_in_stage)))

    return {"data": items}
