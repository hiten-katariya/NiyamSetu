from datetime import date, datetime, timedelta, timezone
from typing import Dict
import uuid
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import get_password_hash
from backend.app.models.entities import (
    Application,
    AuditLog,
    Escalation,
    EscalationRule,
    Holiday,
    Institution,
    Notification,
    Region,
    ReminderRule,
    RouteStage,
    RouteType,
    SchedulerRun,
    StageHistory,
    User,
)
from backend.app.permissions.roles import UserRole
from backend.app.services.deadline_service import DeadlineService
from backend.app.services.escalation_service import EscalationService
from backend.app.services.reminder_service import ReminderService
from backend.app.services.workflow_service import WorkflowService
from worker.deadline_scan import execute_deadline_scan


@pytest.fixture
def phase4_test_setup(db_session: Session) -> Dict:
    """
    Sets up isolated test environment for Phase 4:
    - 2 Regions (North, South)
    - 2 Institutions
    - 1 Active Route with 3 stages (including calendar & working day types, and stage with no timeline)
    - Holidays configured for North region & national
    - Reminder and Escalation rules
    - Users for various roles
    """
    pw = get_password_hash("ValidPassword123!")

    # 1. Regions
    r_north = Region(id=uuid.uuid4(), name="North Region", code="REG_N", is_active=True)
    r_south = Region(id=uuid.uuid4(), name="South Region", code="REG_S", is_active=True)
    db_session.add_all([r_north, r_south])
    db_session.flush()

    # 2. Institutions
    inst_a = Institution(
        id=uuid.uuid4(),
        name="Institute Alpha",
        institution_code="INST-A",
        region_id=r_north.id,
        contact_email="inst_a@test.local",
        is_active=True,
    )
    inst_b = Institution(
        id=uuid.uuid4(),
        name="Institute Beta",
        institution_code="INST-B",
        region_id=r_south.id,
        contact_email="inst_b@test.local",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    db_session.flush()

    # 3. Route & Stages
    route = RouteType(
        id=uuid.uuid4(),
        name="Approval Route",
        code="ROUTE_APP",
        description="Standard approval workflow",
        is_active=True,
        current_version=1,
    )
    db_session.add(route)
    db_session.flush()

    # Stage 1: Working days timeline (5 working days)
    stage1 = RouteStage(
        id=uuid.uuid4(),
        route_type_id=route.id,
        route_version=1,
        stage_code="STG_SCRUTINY",
        stage_name="Document Scrutiny",
        sequence=1,
        required_role=UserRole.SCRUTINY_OFFICER.value,
        timeline_days=5,
        day_type="working",
        is_required=True,
    )
    # Stage 2: Calendar days timeline (7 calendar days)
    stage2 = RouteStage(
        id=uuid.uuid4(),
        route_type_id=route.id,
        route_version=1,
        stage_code="STG_REGIONAL",
        stage_name="Regional Review",
        sequence=2,
        required_role=UserRole.REGIONAL_OFFICER.value,
        timeline_days=7,
        day_type="calendar",
        is_required=True,
    )
    # Stage 3: No configured timeline (0 days)
    stage3 = RouteStage(
        id=uuid.uuid4(),
        route_type_id=route.id,
        route_version=1,
        stage_code="STG_NO_TIMELINE",
        stage_name="Open Ended Review",
        sequence=3,
        required_role=UserRole.SENIOR_AUTHORITY.value,
        timeline_days=0,
        day_type="calendar",
        is_required=False,
    )
    db_session.add_all([stage1, stage2, stage3])
    db_session.flush()

    # 4. Holidays
    # National holiday on Friday 2026-10-23 (region_id is None)
    h_nat = Holiday(
        id=uuid.uuid4(),
        name="National Festival",
        holiday_date=date(2026, 10, 23),
        region_id=None,
    )
    # North Region holiday on Monday 2026-10-26
    h_reg = Holiday(
        id=uuid.uuid4(),
        name="Regional Day",
        holiday_date=date(2026, 10, 26),
        region_id=r_north.id,
    )
    db_session.add_all([h_nat, h_reg])
    db_session.flush()

    # 5. Reminder & Escalation Rules
    rem_rule_2d = ReminderRule(
        id=uuid.uuid4(),
        name="2 Days Approaching Reminder",
        target_type="application",
        days_before_due=2,
        recipient_roles=[UserRole.INSTITUTION_USER.value, UserRole.SCRUTINY_OFFICER.value],
        is_active=True,
    )
    rem_rule_0d = ReminderRule(
        id=uuid.uuid4(),
        name="Due Today Reminder",
        target_type="application",
        days_before_due=0,
        recipient_roles=[UserRole.INSTITUTION_USER.value, UserRole.REGIONAL_OFFICER.value],
        is_active=True,
    )
    esc_rule_tier1 = EscalationRule(
        id=uuid.uuid4(),
        name="Tier 1 Escalation",
        target_type="application",
        level=1,
        days_after_due=1,
        recipient_roles=[UserRole.REGIONAL_OFFICER.value],
        is_active=True,
    )
    esc_rule_tier2 = EscalationRule(
        id=uuid.uuid4(),
        name="Tier 2 Escalation",
        target_type="application",
        level=2,
        days_after_due=3,
        recipient_roles=[UserRole.SENIOR_AUTHORITY.value],
        is_active=True,
    )
    db_session.add_all([rem_rule_2d, rem_rule_0d, esc_rule_tier1, esc_rule_tier2])
    db_session.flush()

    # 6. Users
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@test.local",
        full_name="Admin User",
        password_hash=pw,
        role=UserRole.SYSTEM_ADMIN.value,
        is_active=True,
    )
    inst_user_a = User(
        id=uuid.uuid4(),
        email="inst_a@test.local",
        full_name="Inst User Alpha",
        password_hash=pw,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_a.id,
        region_id=r_north.id,
        is_active=True,
    )
    inst_user_b = User(
        id=uuid.uuid4(),
        email="inst_b@test.local",
        full_name="Inst User Beta",
        password_hash=pw,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_b.id,
        region_id=r_south.id,
        is_active=True,
    )
    scrutiny_user = User(
        id=uuid.uuid4(),
        email="scrutiny@test.local",
        full_name="Scrutiny Officer",
        password_hash=pw,
        role=UserRole.SCRUTINY_OFFICER.value,
        is_active=True,
    )
    ro_north = User(
        id=uuid.uuid4(),
        email="ro_north@test.local",
        full_name="RO North",
        password_hash=pw,
        role=UserRole.REGIONAL_OFFICER.value,
        region_id=r_north.id,
        is_active=True,
    )
    ro_south = User(
        id=uuid.uuid4(),
        email="ro_south@test.local",
        full_name="RO South",
        password_hash=pw,
        role=UserRole.REGIONAL_OFFICER.value,
        region_id=r_south.id,
        is_active=True,
    )
    senior_user = User(
        id=uuid.uuid4(),
        email="senior@test.local",
        full_name="Senior Authority",
        password_hash=pw,
        role=UserRole.SENIOR_AUTHORITY.value,
        is_active=True,
    )

    db_session.add_all([
        admin_user,
        inst_user_a,
        inst_user_b,
        scrutiny_user,
        ro_north,
        ro_south,
        senior_user,
    ])
    db_session.commit()

    return {
        "region_north": r_north,
        "region_south": r_south,
        "inst_a": inst_a,
        "inst_b": inst_b,
        "route": route,
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3,
        "h_nat": h_nat,
        "h_reg": h_reg,
        "admin": admin_user,
        "inst_user_a": inst_user_a,
        "inst_user_b": inst_user_b,
        "scrutiny_user": scrutiny_user,
        "ro_north": ro_north,
        "ro_south": ro_south,
        "senior_user": senior_user,
    }


def login_helper(client: TestClient, email: str, password: str = "ValidPassword123!"):
    """Logs in and returns cookies and CSRF headers."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    csrf_token = res.json()["data"]["csrf_token"]
    session_cookie = res.cookies.get(settings.SESSION_COOKIE_NAME)
    csrf_cookie = res.cookies.get(settings.CSRF_COOKIE_NAME)
    cookies = {settings.SESSION_COOKIE_NAME: session_cookie, settings.CSRF_COOKIE_NAME: csrf_cookie}
    headers = {"X-CSRF-Token": csrf_token}
    return cookies, headers


# ==============================================================================
# Unit Tests: Deadline Service Calculations
# ==============================================================================

def test_calendar_days_deadline():
    """Calendar days simply adds timedelta without skipping weekends."""
    start = datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc)  # Friday
    deadline = DeadlineService.calculate_raw_deadline(start, timeline_days=5, day_type="calendar")
    expected = datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc)  # Wednesday
    assert deadline == expected


def test_working_days_deadline_skipping_weekends():
    """Working days skip Saturday and Sunday."""
    # Friday 2026-10-23 + 2 working days:
    # Sat 24 (skip), Sun 25 (skip) -> Mon 26 (day 1), Tue 27 (day 2)
    start = datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc)
    deadline = DeadlineService.calculate_raw_deadline(start, timeline_days=2, day_type="working")
    expected = datetime(2026, 10, 27, 10, 0, tzinfo=timezone.utc)
    assert deadline == expected


def test_working_days_deadline_skipping_holidays():
    """Working days skip weekends AND configured holidays."""
    # Start: Thursday 2026-10-22
    # Holidays: Friday 2026-10-23
    # Weekend: Sat 24, Sun 25
    # Working days: Mon 26 (day 1), Tue 27 (day 2), Wed 28 (day 3)
    start = datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc)
    holidays = {date(2026, 10, 23)}
    deadline = DeadlineService.calculate_raw_deadline(
        start, timeline_days=3, day_type="working", holiday_dates=holidays
    )
    expected = datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc)
    assert deadline == expected


def test_hold_duration_and_deadline_extension(db_session: Session, phase4_test_setup: dict):
    """
    Putting an application on hold and then resuming it defers the calculated deadline
    by the exact paused duration.
    """
    app = WorkflowService.create_application(
        db=db_session,
        user=phase4_test_setup["inst_user_a"],
        route_type_id=phase4_test_setup["route"].id,
        institution_id=phase4_test_setup["inst_a"].id,
    )
    db_session.flush()

    # Set stage entered 5 days ago so hold period (2 days ago) falls inside stage
    now = datetime.now(timezone.utc)
    app.stage_entered_at = now - timedelta(days=5)
    db_session.commit()

    # Initial deadline without hold
    res_initial = DeadlineService.calculate_application_deadline(db_session, app, as_of_time=now)
    assert res_initial.due_date is not None

    # Simulate hold event from 2 days ago to 1 day ago (24 hours hold)
    hold_start = now - timedelta(days=2)
    resume_time = now - timedelta(days=1)

    h_hold = StageHistory(
        id=uuid.uuid4(),
        application_id=app.id,
        from_stage_id=app.current_stage_id,
        to_stage_id=app.current_stage_id,
        action="hold",
        performed_by_user_id=phase4_test_setup["admin"].id,
        performed_at=hold_start,
        reason="Verification on hold",
    )
    h_resume = StageHistory(
        id=uuid.uuid4(),
        application_id=app.id,
        from_stage_id=app.current_stage_id,
        to_stage_id=app.current_stage_id,
        action="resume",
        performed_by_user_id=phase4_test_setup["admin"].id,
        performed_at=resume_time,
        reason="Resumed after review",
    )
    db_session.add_all([h_hold, h_resume])
    db_session.commit()

    # Calculate hold duration
    hold_seconds = DeadlineService.calculate_hold_duration(db_session, app.id, app.stage_entered_at, as_of_time=now)
    assert abs(hold_seconds - 86400.0) < 5.0  # ~1 day in seconds

    # Calculate new deadline
    res_after_hold = DeadlineService.calculate_application_deadline(db_session, app, as_of_time=now)
    assert res_after_hold.due_date is not None
    deadline_diff = (res_after_hold.due_date - res_initial.due_date).total_seconds()
    assert abs(deadline_diff - 86400.0) < 5.0


def test_missing_timeline_days_handling(db_session: Session, phase4_test_setup: dict):
    """
    Stages without configured timelines (timeline_days is None) return due_date=None
    and are NEVER flagged as overdue.
    """
    app = WorkflowService.create_application(
        db=db_session,
        user=phase4_test_setup["inst_user_a"],
        route_type_id=phase4_test_setup["route"].id,
        institution_id=phase4_test_setup["inst_a"].id,
    )
    # Move application to stage 3 (which has timeline_days=0)
    app.current_stage_id = phase4_test_setup["stage3"].id
    app.current_stage = phase4_test_setup["stage3"]
    app.stage_entered_at = datetime.now(timezone.utc) - timedelta(days=30)
    db_session.commit()

    res = DeadlineService.calculate_application_deadline(db_session, app)
    assert res.due_date is None
    assert res.is_overdue is False
    assert res.days_remaining is None

    # Also test application with no active stage assigned
    app.current_stage_id = None
    app.current_stage = None
    db_session.commit()

    res_no_stage = DeadlineService.calculate_application_deadline(db_session, app)
    assert res_no_stage.due_date is None
    assert res_no_stage.is_overdue is False


def test_completed_application_deadline(db_session: Session, phase4_test_setup: dict):
    """Closed/completed applications do not have active deadlines."""
    app = WorkflowService.create_application(
        db=db_session,
        user=phase4_test_setup["inst_user_a"],
        route_type_id=phase4_test_setup["route"].id,
        institution_id=phase4_test_setup["inst_a"].id,
    )
    app.status = "completed"
    db_session.commit()

    res = DeadlineService.calculate_application_deadline(db_session, app)
    assert res.due_date is None
    assert res.is_overdue is False


# ==============================================================================
# Unit Tests: Reminder & Escalation Engines and Idempotency
# ==============================================================================

def test_reminder_generation_and_deduplication(db_session: Session, phase4_test_setup: dict):
    """
    Reminders are sent to authorized recipients and NOT duplicated on repeated runs.
    """
    app = WorkflowService.create_application(
        db=db_session,
        user=phase4_test_setup["inst_user_a"],
        route_type_id=phase4_test_setup["route"].id,
        institution_id=phase4_test_setup["inst_a"].id,
    )
    # Use stage 2 with 7 calendar days timeline
    app.current_stage_id = phase4_test_setup["stage2"].id
    app.current_stage = phase4_test_setup["stage2"]
    now = datetime.now(timezone.utc)
    # Stage entered 5.5 days ago -> 1.5 days remaining (< 2 days threshold)
    app.stage_entered_at = now - timedelta(days=5, hours=12)
    db_session.commit()

    # First scan
    notifs1 = ReminderService.process_application_reminders(db_session, app, as_of_time=now)
    db_session.commit()
    assert len(notifs1) > 0

    # Ensure notifications were sent to authorized users (inst_user_a and scrutiny_user)
    recipient_ids = {n.recipient_user_id for n in notifs1}
    assert phase4_test_setup["inst_user_a"].id in recipient_ids
    # inst_user_b must NOT receive reminders for inst_a's application
    assert phase4_test_setup["inst_user_b"].id not in recipient_ids

    # Second scan with same as_of time: MUST produce 0 duplicate notifications
    notifs2 = ReminderService.process_application_reminders(db_session, app, as_of_time=now)
    assert len(notifs2) == 0


def test_escalation_generation_and_deduplication(db_session: Session, phase4_test_setup: dict):
    """
    Overdue applications trigger tiered escalations without duplicate open escalations.
    """
    app = WorkflowService.create_application(
        db=db_session,
        user=phase4_test_setup["inst_user_a"],
        route_type_id=phase4_test_setup["route"].id,
        institution_id=phase4_test_setup["inst_a"].id,
    )
    # Stage entered 15 days ago -> overdue by more than 1 day
    app.stage_entered_at = datetime.now(timezone.utc) - timedelta(days=15)
    db_session.commit()

    # First scan triggers escalation
    escs1 = EscalationService.process_application_escalations(db_session, app)
    db_session.commit()
    assert len(escs1) >= 1
    assert escs1[0].status == "open"
    assert escs1[0].level in (1, 2)

    # Repeat scan: must NOT create another open escalation for the same level
    escs2 = EscalationService.process_application_escalations(db_session, app)
    assert len(escs2) == 0


def test_escalation_resolution_and_authorization(db_session: Session, phase4_test_setup: dict):
    """
    Only authorized supervisory officers can resolve escalations; notes are mandatory.
    """
    app = WorkflowService.create_application(
        db=db_session,
        user=phase4_test_setup["inst_user_a"],
        route_type_id=phase4_test_setup["route"].id,
        institution_id=phase4_test_setup["inst_a"].id,
    )
    app.stage_entered_at = datetime.now(timezone.utc) - timedelta(days=15)
    db_session.commit()

    escs = EscalationService.process_application_escalations(db_session, app)
    db_session.commit()
    esc = escs[0]

    # 1. Institution user attempt to resolve must fail
    with pytest.raises(Exception):
        EscalationService.resolve_escalation(
            db=db_session,
            escalation_id=esc.id,
            user=phase4_test_setup["inst_user_a"],
            resolution_notes="Trying to resolve as student/institute",
        )

    # 2. Empty notes attempt must fail
    with pytest.raises(Exception):
        EscalationService.resolve_escalation(
            db=db_session,
            escalation_id=esc.id,
            user=phase4_test_setup["ro_north"],
            resolution_notes="   ",
        )

    # 3. Regional officer from south region cannot resolve north region escalation
    with pytest.raises(Exception):
        EscalationService.resolve_escalation(
            db=db_session,
            escalation_id=esc.id,
            user=phase4_test_setup["ro_south"],
            resolution_notes="Southern officer trying to resolve Northern issue",
        )

    # 4. Authorized regional officer (RO North) resolves successfully
    resolved = EscalationService.resolve_escalation(
        db=db_session,
        escalation_id=esc.id,
        user=phase4_test_setup["ro_north"],
        resolution_notes="Document discrepancy verified and institutional query responded to.",
    )
    assert resolved.status == "resolved"
    assert resolved.resolved_at is not None
    assert resolved.resolution_notes.startswith("Document discrepancy verified")


def test_worker_run_once_execution(db_session: Session, phase4_test_setup: dict):
    """
    Direct test of execute_deadline_scan creating a completed scheduler_runs entry.
    """
    # Create an active application
    WorkflowService.create_application(
        db=db_session,
        user=phase4_test_setup["inst_user_a"],
        route_type_id=phase4_test_setup["route"].id,
        institution_id=phase4_test_setup["inst_a"].id,
    )
    db_session.commit()

    run_entry = execute_deadline_scan(db_session)
    assert run_entry["status"] == "success"
    assert run_entry["items_scanned"] >= 1
    assert run_entry["finished_at"] is not None


# ==============================================================================
# Integration Tests: Notification & Escalation APIs
# ==============================================================================

def test_api_notifications_scoping_and_read(client: TestClient, phase4_test_setup: dict, db_session: Session):
    """
    Users only see their own notifications; can mark individual and all as read.
    """
    # Create notifications for User A and User B
    n_a = Notification(
        id=uuid.uuid4(),
        recipient_user_id=phase4_test_setup["inst_user_a"].id,
        target_type="application",
        target_id=uuid.uuid4(),
        channel="in_app",
        title="Notice A",
        body="Body A",
        status="unread",
        dedupe_key=f"test:{uuid.uuid4()}",
    )
    n_b = Notification(
        id=uuid.uuid4(),
        recipient_user_id=phase4_test_setup["inst_user_b"].id,
        target_type="application",
        target_id=uuid.uuid4(),
        channel="in_app",
        title="Notice B",
        body="Body B",
        status="unread",
        dedupe_key=f"test:{uuid.uuid4()}",
    )
    db_session.add_all([n_a, n_b])
    db_session.commit()

    cookies_a, headers_a = login_helper(client, "inst_a@test.local")

    # 1. User A lists notifications
    res = client.get("/api/v1/notifications", cookies=cookies_a)
    assert res.status_code == 200
    items = res.json()["data"]
    assert any(item["title"] == "Notice A" for item in items)
    assert not any(item["title"] == "Notice B" for item in items)  # Scoped out!

    # 2. Check unread count
    res_count = client.get("/api/v1/notifications/unread-count", cookies=cookies_a)
    assert res_count.status_code == 200
    assert res_count.json()["data"]["unread_count"] >= 1

    # 3. Mark individual as read
    res_read = client.post(f"/api/v1/notifications/{n_a.id}/read", cookies=cookies_a, headers=headers_a)
    assert res_read.status_code == 200
    assert res_read.json()["data"]["status"] == "read"

    # 4. Mark all read
    res_all = client.post("/api/v1/notifications/read-all", cookies=cookies_a, headers=headers_a)
    assert res_all.status_code == 200


def test_api_escalations_listing_and_resolution(client: TestClient, phase4_test_setup: dict, db_session: Session):
    """
    Escalations API lists regionally scoped escalations and allows resolution with notes.
    """
    app = WorkflowService.create_application(
        db=db_session,
        user=phase4_test_setup["inst_user_a"],
        route_type_id=phase4_test_setup["route"].id,
        institution_id=phase4_test_setup["inst_a"].id,
    )
    app.stage_entered_at = datetime.now(timezone.utc) - timedelta(days=20)
    db_session.commit()

    escs = EscalationService.process_application_escalations(db_session, app)
    db_session.commit()
    esc = escs[0]

    # Regional officer North logs in
    cookies_ro, headers_ro = login_helper(client, "ro_north@test.local")

    # List escalations
    res_list = client.get("/api/v1/escalations", cookies=cookies_ro)
    assert res_list.status_code == 200
    esc_items = res_list.json()["data"]
    assert any(item["id"] == str(esc.id) for item in esc_items)

    # Resolve escalation
    res_resolve = client.post(
        f"/api/v1/escalations/{esc.id}/resolve",
        json={"resolution_notes": "SLA breach resolved following committee expedited session."},
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["data"]["status"] == "resolved"


def test_api_dashboard_pendency_and_attention(client: TestClient, phase4_test_setup: dict, db_session: Session):
    """
    Dashboard endpoints return live pendency and prioritized attention items.
    """
    # Create application that is overdue
    app = WorkflowService.create_application(
        db=db_session,
        user=phase4_test_setup["inst_user_a"],
        route_type_id=phase4_test_setup["route"].id,
        institution_id=phase4_test_setup["inst_a"].id,
    )
    app.stage_entered_at = datetime.now(timezone.utc) - timedelta(days=25)
    db_session.commit()

    cookies_admin, _ = login_helper(client, "admin@test.local")

    # 1. Pendency
    res_pendency = client.get("/api/v1/dashboard/pendency", cookies=cookies_admin)
    assert res_pendency.status_code == 200
    data_p = res_pendency.json()["data"]
    assert data_p["total_pending"] >= 1
    assert data_p["overdue_count"] >= 1

    # 2. Attention items
    res_att = client.get("/api/v1/dashboard/attention", cookies=cookies_admin)
    assert res_att.status_code == 200
    att_items = res_att.json()["data"]
    assert len(att_items) >= 1
    # Critical overdue item must be present
    assert any(item["id"] == str(app.id) and item["priority"] == "critical" for item in att_items)

    # 3. Summary
    res_summary = client.get("/api/v1/dashboard/summary", cookies=cookies_admin)
    assert res_summary.status_code == 200
    data_s = res_summary.json()["data"]
    assert data_s["overdue_items"] >= 1
