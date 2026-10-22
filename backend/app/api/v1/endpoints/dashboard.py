from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user
from backend.app.core.exceptions import ForbiddenError
from backend.app.db.session import get_db
from backend.app.models.entities import (
    Application,
    Document,
    DocumentRenewal,
    Escalation,
    EVC,
    EVCReport,
    Institution,
    Notification,
    Region,
    RouteStage,
    SchedulerRun,
    Undertaking,
    User,
)
from backend.app.permissions.roles import UserRole, normalize_role
from backend.app.schemas.common import DataResponse
from backend.app.schemas.dashboard import (
    AgeingMetric,
    AttentionItemResponse,
    DashboardSummary,
    DocumentAnalyticsResponse,
    EVCAnalyticsResponse,
    OperationalSummaryResponse,
    PendencyMetrics,
    RegionalMetricItem,
    UndertakingAnalyticsResponse,
    VolumeTrendPoint,
)
from backend.app.services.deadline_service import DeadlineService

router = APIRouter(dependencies=[Depends(get_current_user)])


def get_scoped_applications_query(
    user: User,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    region_id: Optional[uuid.UUID] = None,
    institution_id: Optional[uuid.UUID] = None,
    route_type_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
):
    """
    Constructs a base application query with proper role, regional scoping, and optional filters applied.
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

    # User-supplied filters (applied if permitted)
    if institution_id and role_enum != UserRole.INSTITUTION_USER:
        stmt = stmt.where(Application.institution_id == institution_id)

    if region_id and role_enum not in (UserRole.INSTITUTION_USER, UserRole.REGIONAL_OFFICER):
        stmt = stmt.join(Application.institution).where(Institution.region_id == region_id)

    if route_type_id:
        stmt = stmt.where(Application.route_type_id == route_type_id)

    if status:
        stmt = stmt.where(Application.status == status)

    if start_date:
        stmt = stmt.where(func.date(Application.created_at) >= start_date)

    if end_date:
        stmt = stmt.where(func.date(Application.created_at) <= end_date)

    return stmt


@router.get("/summary", response_model=DataResponse[DashboardSummary], summary="Dashboard Summary Metrics")
def get_dashboard_summary(
    start_date: Optional[date] = Query(None, description="Filter from created date"),
    end_date: Optional[date] = Query(None, description="Filter to created date"),
    region_id: Optional[uuid.UUID] = Query(None, description="Filter by region"),
    institution_id: Optional[uuid.UUID] = Query(None, description="Filter by institution"),
    route_type_id: Optional[uuid.UUID] = Query(None, description="Filter by route type"),
    status: Optional[str] = Query(None, description="Filter by application status"),
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

    if institution_id and role_enum != UserRole.INSTITUTION_USER:
        app_query = app_query.where(Application.institution_id == institution_id)

    if region_id and role_enum not in (UserRole.INSTITUTION_USER, UserRole.REGIONAL_OFFICER):
        app_query = app_query.join(Application.institution).where(Institution.region_id == region_id)

    if route_type_id:
        app_query = app_query.where(Application.route_type_id == route_type_id)

    if status:
        app_query = app_query.where(Application.status == status)

    if start_date:
        app_query = app_query.where(func.date(Application.created_at) >= start_date)

    if end_date:
        app_query = app_query.where(func.date(Application.created_at) <= end_date)

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
                evc_query.where(EVC.status.in_(["queued", "scheduled", "conducted"])).subquery()
            )
        )
        or 0
    )
    pending_undertakings = (
        db.scalar(
            select(func.count()).select_from(
                undertaking_query.where(Undertaking.status.in_(["pending", "submitted", "returned", "overdue"])).subquery()
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
    active_apps_stmt = get_scoped_applications_query(
        current_user,
        start_date=start_date,
        end_date=end_date,
        region_id=region_id,
        institution_id=institution_id,
        route_type_id=route_type_id,
    ).where(Application.status.in_(["in_progress", "returned"]))
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
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    region_id: Optional[uuid.UUID] = Query(None),
    institution_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns real stage ageing distribution calculated by the Deadline Engine for active applications.
    """
    active_apps_stmt = get_scoped_applications_query(
        current_user, start_date=start_date, end_date=end_date, region_id=region_id, institution_id=institution_id
    ).where(Application.status.in_(["in_progress", "returned"]))
    active_apps = list(db.scalars(active_apps_stmt).all())
    now = datetime.now(timezone.utc)

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
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    region_id: Optional[uuid.UUID] = Query(None),
    institution_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns detailed pendency analytics aggregated by stage, region, and SLA urgency.
    """
    active_apps_stmt = get_scoped_applications_query(
        current_user, start_date=start_date, end_date=end_date, region_id=region_id, institution_id=institution_id
    ).where(Application.status.in_(["in_progress", "returned", "on_hold"]))
    active_apps = list(db.scalars(active_apps_stmt).all())
    now = datetime.now(timezone.utc)

    by_stage: Dict[str, int] = defaultdict(int)
    by_region: Dict[str, int] = defaultdict(int)
    overdue_count = 0
    on_hold_count = 0
    due_soon_count = 0

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


@router.get("/volume-trends", response_model=DataResponse[List[VolumeTrendPoint]], summary="Application Volume Trends")
def get_volume_trends(
    days: int = Query(30, ge=7, le=180, description="Number of past days to aggregate"),
    region_id: Optional[uuid.UUID] = Query(None),
    institution_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns daily volume trends of submitted and completed applications over the specified window.
    """
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).date()

    stmt = get_scoped_applications_query(current_user, region_id=region_id, institution_id=institution_id)
    apps = list(db.scalars(stmt).all())

    # Build daily buckets
    points: Dict[str, Dict[str, int]] = {}
    for i in range(days + 1):
        dt = (now - timedelta(days=days - i)).strftime("%Y-%m-%d")
        points[dt] = {"submitted": 0, "completed": 0}

    for app in apps:
        if app.submitted_at:
            s_date = app.submitted_at.strftime("%Y-%m-%d")
            if s_date in points:
                points[s_date]["submitted"] += 1
        elif app.created_at:
            c_date = app.created_at.strftime("%Y-%m-%d")
            if c_date in points:
                points[c_date]["submitted"] += 1

        if app.status == "completed" and app.closed_at:
            cl_date = app.closed_at.strftime("%Y-%m-%d")
            if cl_date in points:
                points[cl_date]["completed"] += 1

    result = [
        VolumeTrendPoint(date=dt, submitted=data["submitted"], completed=data["completed"])
        for dt, data in sorted(points.items())
    ]
    return {"data": result}


@router.get("/regional-comparison", response_model=DataResponse[List[RegionalMetricItem]], summary="Regional Performance Comparison")
def get_regional_comparison(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns regional breakdown of applications, pendency, and overdue volume.
    Strictly restricted to users with regional or multi-regional jurisdiction.
    Institution users are forbidden from accessing regional comparison.
    """
    role_enum = normalize_role(current_user.role)

    if role_enum == UserRole.INSTITUTION_USER:
        raise ForbiddenError("Institutions do not have permission to view cross-regional comparisons")

    # Determine permitted regions
    if role_enum == UserRole.REGIONAL_OFFICER:
        if not current_user.region_id:
            return {"data": []}
        regions = db.scalars(select(Region).where(Region.id == current_user.region_id)).all()
    else:
        # Bureau, Senior Authority, Admin, System Admin
        regions = db.scalars(select(Region).where(Region.is_active == True).order_by(Region.name.asc())).all()

    now = datetime.now(timezone.utc)
    results: List[RegionalMetricItem] = []

    for reg in regions:
        # Query applications for institutions in this region
        apps_stmt = (
            select(Application)
            .join(Application.institution)
            .where(Institution.region_id == reg.id)
            .options(joinedload(Application.institution), joinedload(Application.current_stage))
        )
        apps = list(db.scalars(apps_stmt).all())

        total = len(apps)
        in_prog = sum(1 for a in apps if a.status in ("in_progress", "submitted", "returned", "on_hold"))
        completed = sum(1 for a in apps if a.status == "completed")

        overdue = 0
        for a in apps:
            if a.status in ("in_progress", "returned"):
                res = DeadlineService.calculate_application_deadline(db, a, as_of_time=now)
                if res.is_overdue:
                    overdue += 1

        results.append(
            RegionalMetricItem(
                region_id=reg.id,
                region_name=reg.name,
                total_applications=total,
                in_progress=in_prog,
                overdue=overdue,
                completed=completed,
            )
        )

    return {"data": results}


@router.get("/evc-analytics", response_model=DataResponse[EVCAnalyticsResponse], summary="EVC Operational Analytics")
def get_evc_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns granular metrics on EVC visits, reports, and recommendations.
    """
    role_enum = normalize_role(current_user.role)
    evc_query = select(EVC)

    if role_enum == UserRole.INSTITUTION_USER:
        evc_query = evc_query.join(Application).where(Application.institution_id == current_user.institution_id)
    elif role_enum == UserRole.REGIONAL_OFFICER:
        evc_query = evc_query.where(EVC.assigned_region_id == current_user.region_id)

    evcs = list(db.scalars(evc_query).all())
    evc_ids = [e.id for e in evcs]

    scheduled_count = sum(1 for e in evcs if e.status in ("scheduled", "rescheduled"))
    conducted_count = sum(1 for e in evcs if e.status in ("conducted", "report_submitted", "completed"))

    # Reports
    reports_stmt = select(EVCReport)
    if evc_ids:
        reports_stmt = reports_stmt.where(EVCReport.evc_id.in_(evc_ids))
    else:
        reports_stmt = reports_stmt.where(EVCReport.id == None)

    reports = list(db.scalars(reports_stmt).all())

    pending_reports = sum(1 for r in reports if r.review_status == "pending_review")
    reviewed_reports = sum(1 for r in reports if r.review_status in ("accepted", "returned_for_correction"))

    recommended_count = sum(1 for r in reports if r.review_status == "accepted")
    conditions_count = sum(1 for r in reports if r.review_status == "returned_for_correction")
    not_recommended_count = sum(1 for r in reports if getattr(r, "recommendation", "") == "not_recommended")

    return {
        "data": EVCAnalyticsResponse(
            scheduled_count=scheduled_count,
            conducted_count=conducted_count,
            pending_reports=pending_reports,
            reviewed_reports=reviewed_reports,
            recommended_count=recommended_count,
            conditions_count=conditions_count,
            not_recommended_count=not_recommended_count,
        )
    }


@router.get("/undertaking-analytics", response_model=DataResponse[UndertakingAnalyticsResponse], summary="Undertaking Compliance Analytics")
def get_undertaking_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns status breakdown for institutional compliance undertakings.
    """
    role_enum = normalize_role(current_user.role)
    stmt = select(Undertaking)

    if role_enum == UserRole.INSTITUTION_USER:
        stmt = stmt.where(Undertaking.assigned_institution_id == current_user.institution_id)
    elif role_enum == UserRole.REGIONAL_OFFICER:
        stmt = stmt.join(Institution, Undertaking.assigned_institution_id == Institution.id).where(
            Institution.region_id == current_user.region_id
        )

    items = list(db.scalars(stmt).all())

    return {
        "data": UndertakingAnalyticsResponse(
            total_conditions=len(items),
            pending_evidence=sum(1 for u in items if u.status == "pending"),
            submitted_under_review=sum(1 for u in items if u.status == "submitted"),
            fulfilled=sum(1 for u in items if u.status == "fulfilled"),
            overdue=sum(1 for u in items if u.status == "overdue"),
            returned=sum(1 for u in items if u.status == "returned"),
        )
    }


@router.get("/document-analytics", response_model=DataResponse[DocumentAnalyticsResponse], summary="Document Validity Analytics")
def get_document_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns document validity, expiry, and renewal activity metrics.
    """
    role_enum = normalize_role(current_user.role)
    stmt = select(Document)

    if role_enum == UserRole.INSTITUTION_USER:
        stmt = stmt.where(Document.institution_id == current_user.institution_id)
    elif role_enum == UserRole.REGIONAL_OFFICER:
        stmt = stmt.join(Institution, Document.institution_id == Institution.id).where(
            Institution.region_id == current_user.region_id
        )

    docs = list(db.scalars(stmt).all())
    today = date.today()
    in_30_days = today + timedelta(days=30)

    valid_count = 0
    expiring_soon_count = 0
    expired_count = 0
    pending_verify = 0

    for doc in docs:
        if doc.verification_status == "pending_verification":
            pending_verify += 1

        if doc.valid_to:
            if doc.valid_to < today or doc.verification_status == "expired":
                expired_count += 1
            elif doc.valid_to <= in_30_days:
                expiring_soon_count += 1
            elif doc.verification_status == "verified":
                valid_count += 1
        elif doc.verification_status == "verified":
            valid_count += 1

    # Active renewals
    doc_ids = [d.id for d in docs]
    active_renewals = 0
    if doc_ids:
        active_renewals = (
            db.scalar(
                select(func.count(DocumentRenewal.id)).where(
                    DocumentRenewal.document_id.in_(doc_ids),
                    DocumentRenewal.status.in_(["initiated", "in_progress"]),
                )
            )
            or 0
        )

    return {
        "data": DocumentAnalyticsResponse(
            valid_count=valid_count,
            expiring_soon_count=expiring_soon_count,
            expired_count=expired_count,
            pending_verification_count=pending_verify,
            renewals_in_progress=active_renewals,
        )
    }


@router.get("/operational-summary", response_model=DataResponse[OperationalSummaryResponse], summary="Operational Monitoring Summary")
def get_operational_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns operational diagnostic metrics: escalations, notifications, and background scheduler health.
    """
    role_enum = normalize_role(current_user.role)

    # Escalations
    esc_stmt = select(Escalation)
    if role_enum == UserRole.REGIONAL_OFFICER:
        esc_stmt = esc_stmt.join(Application).join(Application.institution).where(
            Institution.region_id == current_user.region_id
        )
    elif role_enum == UserRole.INSTITUTION_USER:
        esc_stmt = esc_stmt.join(Application).where(Application.institution_id == current_user.institution_id)

    escalations = list(db.scalars(esc_stmt).all())
    open_esc = sum(1 for e in escalations if e.status == "open")
    resolved_esc = sum(1 for e in escalations if e.status == "resolved")

    # Notifications
    notif_stmt = select(Notification)
    if role_enum == UserRole.INSTITUTION_USER:
        notif_stmt = notif_stmt.where(Notification.recipient_user_id == current_user.id)
    notifications = list(db.scalars(notif_stmt).all())
    unread_notifs = sum(1 for n in notifications if n.status == "unread")
    total_notifs = len(notifications)

    # Scheduler Runs
    last_run_stmt = select(SchedulerRun).order_by(SchedulerRun.started_at.desc()).limit(1)
    last_run = db.scalars(last_run_stmt).first()

    worker_status = "never_run"
    last_scan_at = None
    if last_run:
        last_scan_at = last_run.started_at
        now = datetime.now(timezone.utc)
        run_time = last_run.started_at
        if run_time.tzinfo is None:
            run_time = run_time.replace(tzinfo=timezone.utc)

        if last_run.status == "failed":
            worker_status = "failed"
        elif (now - run_time).total_seconds() > 3600:
            worker_status = "stale"
        else:
            worker_status = "operational"

    fail_count = (
        db.scalar(select(func.count(SchedulerRun.id)).where(SchedulerRun.status == "failed")) or 0
    )

    return {
        "data": OperationalSummaryResponse(
            open_escalations=open_esc,
            resolved_escalations=resolved_esc,
            unread_notifications=unread_notifs,
            total_notifications=total_notifs,
            worker_status=worker_status,
            last_scan_at=last_scan_at,
            failure_count=fail_count,
        )
    }


@router.get("/attention", response_model=DataResponse[List[AttentionItemResponse]], summary="Items Requiring Immediate Attention")
def get_attention_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns priority-ranked items requiring human intervention.
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
