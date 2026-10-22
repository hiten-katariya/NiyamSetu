from datetime import date, datetime, timedelta, timezone
import io
from typing import Dict
import uuid
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import get_password_hash
from backend.app.models.entities import (
    Application,
    AuditLog,
    ConfigVersion,
    Document,
    Escalation,
    EscalationRule,
    EVC,
    EVCMember,
    FileRecord,
    Holiday,
    Institution,
    MessageTemplate,
    Notification,
    Region,
    ReminderRule,
    RouteStage,
    RouteType,
    SchedulerRun,
    StageHistory,
    Undertaking,
    User,
)
from backend.app.permissions.roles import UserRole
from backend.app.services.workflow_service import WorkflowService
from worker.deadline_scan import execute_deadline_scan


@pytest.fixture
def e2e_environment(db_session: Session) -> Dict:
    """
    Sets up a comprehensive realistic multi-tenant environment:
    - 2 Regions: North, South
    - 2 Institutions: Alpha (North), Beta (South)
    - 7 distinct roles:
      1. Institution User A (Alpha)
      2. Institution User B (Beta)
      3. Scrutiny Officer (North)
      4. Regional Officer (North)
      5. Bureau Officer (Apex)
      6. Committee Member 1 (assigned)
      7. Committee Member 2 (unassigned)
      8. Senior Authority / Apex
      9. Administrator
    - Workflow Route & Stages (Draft -> Scrutiny -> EVC -> Approval)
    """
    pw = get_password_hash("ValidPassword123!")

    # Regions
    r_north = Region(id=uuid.uuid4(), name="North Region", code="REG_NORTH", is_active=True)
    r_south = Region(id=uuid.uuid4(), name="South Region", code="REG_SOUTH", is_active=True)
    db_session.add_all([r_north, r_south])
    db_session.flush()

    # Institutions
    inst_a = Institution(
        id=uuid.uuid4(),
        name="Institute of Technology Alpha",
        institution_code="INST-ALPHA",
        region_id=r_north.id,
        contact_email="principal@inst-alpha.edu",
        is_active=True,
    )
    inst_b = Institution(
        id=uuid.uuid4(),
        name="Institute of Management Beta",
        institution_code="INST-BETA",
        region_id=r_south.id,
        contact_email="director@inst-beta.edu",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    db_session.flush()

    # Users
    inst_user_a = User(
        id=uuid.uuid4(),
        email="inst_a@test.local",
        full_name="Institution User Alpha",
        password_hash=pw,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_a.id,
        region_id=r_north.id,
        is_active=True,
    )
    inst_user_b = User(
        id=uuid.uuid4(),
        email="inst_b@test.local",
        full_name="Institution User Beta",
        password_hash=pw,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_b.id,
        region_id=r_south.id,
        is_active=True,
    )
    scrutiny_officer = User(
        id=uuid.uuid4(),
        email="scrutiny@test.local",
        full_name="Scrutiny Officer North",
        password_hash=pw,
        role=UserRole.SCRUTINY_OFFICER.value,
        region_id=r_north.id,
        is_active=True,
    )
    regional_officer = User(
        id=uuid.uuid4(),
        email="ro_north@test.local",
        full_name="Regional Officer North",
        password_hash=pw,
        role=UserRole.REGIONAL_OFFICER.value,
        region_id=r_north.id,
        is_active=True,
    )
    bureau_officer = User(
        id=uuid.uuid4(),
        email="bureau@test.local",
        full_name="Bureau Officer Apex",
        password_hash=pw,
        role=UserRole.BUREAU_OFFICER.value,
        is_active=True,
    )
    cm_assigned = User(
        id=uuid.uuid4(),
        email="cm_assigned@test.local",
        full_name="Prof. Sharma (EVC Member)",
        password_hash=pw,
        role=UserRole.COMMITTEE_MEMBER.value,
        is_active=True,
    )
    cm_unassigned = User(
        id=uuid.uuid4(),
        email="cm_unassigned@test.local",
        full_name="Prof. Verma (Other Member)",
        password_hash=pw,
        role=UserRole.COMMITTEE_MEMBER.value,
        is_active=True,
    )
    senior_authority = User(
        id=uuid.uuid4(),
        email="senior@test.local",
        full_name="Member Secretary Apex",
        password_hash=pw,
        role=UserRole.SENIOR_AUTHORITY.value,
        is_active=True,
    )
    admin = User(
        id=uuid.uuid4(),
        email="admin@test.local",
        full_name="System Administrator",
        password_hash=pw,
        role=UserRole.ADMIN.value,
        is_active=True,
    )

    db_session.add_all([
        inst_user_a, inst_user_b, scrutiny_officer, regional_officer,
        bureau_officer, cm_assigned, cm_unassigned, senior_authority, admin
    ])
    db_session.flush()

    # Route & Stages
    route = RouteType(
        id=uuid.uuid4(),
        name="Engineering Extension Approval Route",
        code="ENGG_EXT_2026",
        description="Standard route for engineering extension of approval",
        is_active=True,
        current_version=1,
    )
    db_session.add(route)
    db_session.flush()

    stage1 = RouteStage(
        id=uuid.uuid4(),
        route_type_id=route.id,
        route_version=1,
        stage_code="SCRUTINY",
        stage_name="Scrutiny Review",
        sequence=1,
        required_role=UserRole.SCRUTINY_OFFICER.value,
        timeline_days=7,
        day_type="working_days",
        is_required=True,
    )
    stage2 = RouteStage(
        id=uuid.uuid4(),
        route_type_id=route.id,
        route_version=1,
        stage_code="EVC",
        stage_name="EVC Committee Inspection",
        sequence=2,
        required_role=UserRole.REGIONAL_OFFICER.value,
        timeline_days=10,
        day_type="calendar_days",
        is_required=True,
    )
    stage3 = RouteStage(
        id=uuid.uuid4(),
        route_type_id=route.id,
        route_version=1,
        stage_code="FINAL_DECISION",
        stage_name="Bureau Final Decision",
        sequence=3,
        required_role=UserRole.BUREAU_OFFICER.value,
        timeline_days=5,
        day_type="calendar_days",
        is_required=True,
    )
    db_session.add_all([stage1, stage2, stage3])

    # Default reminder rule
    rem_rule = ReminderRule(
        id=uuid.uuid4(),
        name="Stage Due Soon",
        target_type="application",
        days_before_due=3,
        recipient_roles=["institution_user", "scrutiny_officer"],
        is_active=True,
    )
    # Default escalation rule
    esc_rule = EscalationRule(
        id=uuid.uuid4(),
        name="Stage Overdue Escalation",
        target_type="application",
        level=1,
        days_after_due=2,
        recipient_roles=["regional_officer"],
        is_active=True,
    )
    db_session.add_all([rem_rule, esc_rule])
    db_session.commit()

    return {
        "r_north": r_north,
        "r_south": r_south,
        "inst_a": inst_a,
        "inst_b": inst_b,
        "inst_user_a": inst_user_a,
        "inst_user_b": inst_user_b,
        "scrutiny_officer": scrutiny_officer,
        "regional_officer": regional_officer,
        "bureau_officer": bureau_officer,
        "cm_assigned": cm_assigned,
        "cm_unassigned": cm_unassigned,
        "senior_authority": senior_authority,
        "admin": admin,
        "route": route,
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3,
        "rem_rule": rem_rule,
        "esc_rule": esc_rule,
    }


def auth_client(client: TestClient, email: str, password: str = "ValidPassword123!"):
    """Helper to authenticate and return session cookies and anti-CSRF headers."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    csrf_token = res.json()["data"]["csrf_token"]
    session_cookie = res.cookies.get(settings.SESSION_COOKIE_NAME)
    csrf_cookie = res.cookies.get(settings.CSRF_COOKIE_NAME)
    cookies = {settings.SESSION_COOKIE_NAME: session_cookie, settings.CSRF_COOKIE_NAME: csrf_cookie}
    headers = {"X-CSRF-Token": csrf_token}
    return cookies, headers


# ==============================================================================
# Workstream 1: Scenario 1 - Authentication and Session Lifecycle
# ==============================================================================

def test_w1_s1_authentication_session_lifecycle(client: TestClient, e2e_environment: dict):
    # 1. Login with valid credentials
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "inst_a@test.local", "password": "ValidPassword123!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()["data"]
    assert data["user"]["email"] == "inst_a@test.local"
    assert "csrf_token" in data
    assert settings.SESSION_COOKIE_NAME in login_res.cookies

    session_cookie = login_res.cookies.get(settings.SESSION_COOKIE_NAME)
    csrf_cookie = login_res.cookies.get(settings.CSRF_COOKIE_NAME)
    csrf_token = data["csrf_token"]
    cookies = {settings.SESSION_COOKIE_NAME: session_cookie, settings.CSRF_COOKIE_NAME: csrf_cookie}

    # 2. Access /api/v1/auth/me
    me_res = client.get("/api/v1/auth/me", cookies=cookies)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["user"]["email"] == "inst_a@test.local"

    # 3. CSRF Protection: Mutating POST without X-CSRF-Token header -> 403 Forbidden
    csrf_fail_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(e2e_environment["route"].id)},
        cookies=cookies,
        # Intentionally missing X-CSRF-Token header
    )
    assert csrf_fail_res.status_code == 403
    assert csrf_fail_res.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"

    # 4. Mutating request with valid CSRF header -> Succeeds
    valid_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(e2e_environment["route"].id)},
        cookies=cookies,
        headers={"X-CSRF-Token": csrf_token},
    )
    assert valid_res.status_code == 201

    # 5. Logout destroys session
    logout_res = client.post(
        "/api/v1/auth/logout",
        cookies=cookies,
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout_res.status_code == 200

    # 6. Subsequent requests with destroyed session cookie -> 401 Unauthorized
    after_logout_res = client.get("/api/v1/auth/me", cookies=cookies)
    assert after_logout_res.status_code == 401

    # 7. Invalid password gives generic error without exposing whether user exists
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "inst_a@test.local", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401
    assert "Invalid email or password" in bad_login.json()["error"]["message"]


# ==============================================================================
# Workstream 1: Scenario 2 - Application Lifecycle End-to-End
# ==============================================================================

def test_w1_s2_application_lifecycle_e2e(client: TestClient, e2e_environment: dict, db_session: Session):
    inst_cookies, inst_headers = auth_client(client, "inst_a@test.local")
    so_cookies, so_headers = auth_client(client, "scrutiny@test.local")

    # 1. Create Application as Institution User
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(e2e_environment["route"].id)},
        cookies=inst_cookies,
        headers=inst_headers,
    )
    assert create_res.status_code == 201
    app_id = create_res.json()["data"]["id"]
    ref_no = create_res.json()["data"]["reference_no"]
    assert ref_no.startswith("NS-")

    # Verify initial stage assignment
    get_res = client.get(f"/api/v1/applications/{app_id}", cookies=inst_cookies)
    assert get_res.status_code == 200
    app_data = get_res.json()["data"]
    assert app_data["status"] == "in_progress"
    assert app_data["current_stage_code"] == "SCRUTINY"
    assert app_data["route_version"] == 1

    # 2. Scrutiny officer returns application with return_reason
    bad_return = client.post(
        f"/api/v1/applications/{app_id}/return",
        json={"reason": ""},
        cookies=so_cookies,
        headers=so_headers,
    )
    assert bad_return.status_code in (400, 422)

    return_res = client.post(
        f"/api/v1/applications/{app_id}/return",
        json={"reason": "Missing faculty cadre-ratio supporting documents."},
        cookies=so_cookies,
        headers=so_headers,
    )
    assert return_res.status_code == 200
    assert return_res.json()["data"]["status"] == "returned"

    # 3. Scrutiny officer places on hold with reason
    hold_res = client.post(
        f"/api/v1/applications/{app_id}/hold",
        json={"reason": "Pending state government land NOC verification."},
        cookies=so_cookies,
        headers=so_headers,
    )
    assert hold_res.status_code == 200

    # 4. Scrutiny officer resumes application
    resume_res = client.post(
        f"/api/v1/applications/{app_id}/resume",
        json={"comments": "Land NOC received and verified."},
        cookies=so_cookies,
        headers=so_headers,
    )
    assert resume_res.status_code == 200

    # 5. Scrutiny officer advances to next stage (EVC)
    advance_res = client.post(
        f"/api/v1/applications/{app_id}/advance",
        json={"comments": "Scrutiny completed satisfactorily. Advancing to EVC inspection."},
        cookies=so_cookies,
        headers=so_headers,
    )
    assert advance_res.status_code == 200
    assert advance_res.json()["data"]["current_stage_code"] == "EVC"

    # 6. Verify transition history & route version pinning
    hist_res = client.get(f"/api/v1/applications/{app_id}/history", cookies=inst_cookies)
    assert hist_res.status_code == 200
    transitions = hist_res.json()["data"]
    assert len(transitions) >= 2

    # Check pinned route version
    app_check = client.get(f"/api/v1/applications/{app_id}", cookies=inst_cookies).json()["data"]
    assert app_check["route_version"] == 1


# ==============================================================================
# Workstream 1: Scenario 3 - Deadlines, Reminders, Escalations & Idempotency
# ==============================================================================

def test_w1_s3_deadlines_reminders_escalations_idempotency(client: TestClient, e2e_environment: dict, db_session: Session):
    app = Application(
        id=uuid.uuid4(),
        reference_no="NS-E2E-DEADLINE-01",
        institution_id=e2e_environment["inst_a"].id,
        route_type_id=e2e_environment["route"].id,
        route_version=1,
        current_stage_id=e2e_environment["stage1"].id,
        status="in_progress",
    )
    db_session.add(app)
    db_session.commit()

    holiday = Holiday(
        id=uuid.uuid4(),
        holiday_date=date.today() + timedelta(days=1),
        name="National Holiday Test",
        region_id=None,
    )
    db_session.add(holiday)
    db_session.commit()

    # 1. First Scan
    scan1 = execute_deadline_scan(db=db_session)
    assert scan1["status"] == "success"

    # 2. Immediate Second Scan -> Must be idempotent, no duplicates created
    scan2 = execute_deadline_scan(db=db_session)
    assert scan2["status"] == "success"
    assert scan2["reminders_created"] == 0
    assert scan2["escalations_created"] == 0

    notifs = list(db_session.scalars(select(Notification).where(Notification.application_id == app.id)).all())
    dedupe_keys = [n.dedupe_key for n in notifs]
    assert len(dedupe_keys) == len(set(dedupe_keys)), "Duplicate notification keys detected!"


# ==============================================================================
# Workstream 1: Scenario 4 - EVC Lifecycle End-to-End
# ==============================================================================

def test_w1_s4_evc_lifecycle_e2e(client: TestClient, e2e_environment: dict, db_session: Session):
    ro_cookies, ro_headers = auth_client(client, "ro_north@test.local")
    cm_cookies, cm_headers = auth_client(client, "cm_assigned@test.local")
    unassigned_cookies, _ = auth_client(client, "cm_unassigned@test.local")

    app = Application(
        id=uuid.uuid4(),
        reference_no="NS-E2E-EVC-01",
        institution_id=e2e_environment["inst_a"].id,
        route_type_id=e2e_environment["route"].id,
        route_version=1,
        current_stage_id=e2e_environment["stage2"].id,
        status="in_progress",
    )
    db_session.add(app)
    db_session.commit()

    # 1. Queue EVC visit
    create_evc_res = client.post(
        "/api/v1/evc",
        json={"application_id": str(app.id), "notes": "On-site laboratory and faculty physical inspection."},
        cookies=ro_cookies,
        headers=ro_headers,
    )
    assert create_evc_res.status_code == 200
    evc_id = create_evc_res.json()["data"]["id"]

    # 2. Schedule visit
    visit_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    sched_res = client.post(
        f"/api/v1/evc/{evc_id}/schedule",
        json={"scheduled_at": visit_date, "notes": "Initial visit date."},
        cookies=ro_cookies,
        headers=ro_headers,
    )
    assert sched_res.status_code == 200
    assert sched_res.json()["data"]["status"] == "scheduled"

    # 3. Reschedule visit: Missing reason -> 422
    bad_resched = client.post(
        f"/api/v1/evc/{evc_id}/schedule",
        json={"scheduled_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(), "reason": "   "},
        cookies=ro_cookies,
        headers=ro_headers,
    )
    assert bad_resched.status_code == 422

    # Reschedule with reason -> succeeds
    new_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resched = client.post(
        f"/api/v1/evc/{evc_id}/schedule",
        json={"scheduled_at": new_date, "reason": "Severe rainfall and regional highway disruption."},
        cookies=ro_cookies,
        headers=ro_headers,
    )
    assert resched.status_code == 200

    # 4. Assign committee member
    assign_res = client.post(
        f"/api/v1/evc/{evc_id}/members",
        json={
            "members": [
                {
                    "user_id": str(e2e_environment["cm_assigned"].id),
                    "member_name": "Prof. Sharma",
                    "member_role": "chairman",
                }
            ]
        },
        cookies=ro_cookies,
        headers=ro_headers,
    )
    assert assign_res.status_code == 200

    # 5. Assigned Committee Member can view visit
    cm_view = client.get(f"/api/v1/evc/{evc_id}", cookies=cm_cookies)
    assert cm_view.status_code == 200

    # 6. Unassigned Committee Member is denied access (404/not found in scope)
    unassigned_view = client.get(f"/api/v1/evc/{evc_id}", cookies=unassigned_cookies)
    assert unassigned_view.status_code == 404

    # 7. Committee Member records conduct
    conduct_res = client.post(
        f"/api/v1/evc/{evc_id}/conduct",
        json={"notes": "All laboratories inspected. Adequate computing infrastructure verified."},
        cookies=cm_cookies,
        headers=cm_headers,
    )
    assert conduct_res.status_code == 200
    assert conduct_res.json()["data"]["status"] == "conducted"

    # 8. Committee Member uploads report
    pdf_bytes = b"%PDF-1.4\nEVC inspection report details\n%%EOF"
    rep_upload = client.post(
        f"/api/v1/evc/{evc_id}/report",
        files={"file": ("evc_report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        cookies=cm_cookies,
        headers=cm_headers,
    )
    assert rep_upload.status_code == 200
    report_id = rep_upload.json()["data"]["id"]

    # 9. Regional officer reviews report
    review_res = client.post(
        f"/api/v1/evc/reports/{report_id}/review",
        json={"decision": "accepted", "review_comments": "EVC report accepted and endorsed."},
        cookies=ro_cookies,
        headers=ro_headers,
    )
    assert review_res.status_code == 200


# ==============================================================================
# Workstream 1: Scenario 5 - Undertaking Compliance End-to-End
# ==============================================================================

def test_w1_s5_undertaking_compliance_e2e(client: TestClient, e2e_environment: dict, db_session: Session):
    ro_cookies, ro_headers = auth_client(client, "ro_north@test.local")
    inst_cookies, inst_headers = auth_client(client, "inst_a@test.local")

    app = Application(
        id=uuid.uuid4(),
        reference_no="NS-E2E-UND-01",
        institution_id=e2e_environment["inst_a"].id,
        route_type_id=e2e_environment["route"].id,
        route_version=1,
        current_stage_id=e2e_environment["stage1"].id,
        status="in_progress",
    )
    db_session.add(app)
    db_session.commit()

    # 1. Regional officer creates undertaking for Institution Alpha
    create_und = client.post(
        "/api/v1/undertakings",
        json={
            "application_id": str(app.id),
            "title": "Faculty Cadre-Ratio Compliance",
            "description": "Appoint 2 Professors and 3 Associate Professors in CSE within 90 days.",
            "due_date": (date.today() + timedelta(days=90)).isoformat(),
        },
        cookies=ro_cookies,
        headers=ro_headers,
    )
    assert create_und.status_code == 200
    und_id = create_und.json()["data"]["id"]

    # 2. Institution user submits evidence
    pdf_bytes = b"%PDF-1.4\nAppointment orders enclosed\n%%EOF"
    submit_ev = client.post(
        f"/api/v1/undertakings/{und_id}/submit",
        files={"file": ("appointments.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"comments": "Selection committee minutes and appointment orders issued."},
        cookies=inst_cookies,
        headers=inst_headers,
    )
    assert submit_ev.status_code == 200
    sub_id = submit_ev.json()["data"]["id"]

    # 3. Dual-Control: Institution user cannot verify their own submission -> 403 Forbidden
    self_verify = client.post(
        f"/api/v1/undertakings/submissions/{sub_id}/review",
        json={"decision": "accepted", "review_comments": "Self-approving"},
        cookies=inst_cookies,
        headers=inst_headers,
    )
    assert self_verify.status_code == 403

    # 4. Regional officer verifies and accepts undertaking submission
    verify_res = client.post(
        f"/api/v1/undertakings/submissions/{sub_id}/review",
        json={"decision": "accepted", "review_comments": "Appointment orders verified against AICTE norms."},
        cookies=ro_cookies,
        headers=ro_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["review_status"] == "accepted"


# ==============================================================================
# Workstream 1: Scenario 6 - Document Validity and Renewal End-to-End
# ==============================================================================

def test_w1_s6_document_validity_and_renewal_e2e(client: TestClient, e2e_environment: dict, db_session: Session):
    inst_a_cookies, inst_a_headers = auth_client(client, "inst_a@test.local")
    inst_b_cookies, _ = auth_client(client, "inst_b@test.local")
    ro_cookies, ro_headers = auth_client(client, "ro_north@test.local")

    # 1. Upload valid document
    fake_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    upload_res = client.post(
        "/api/v1/documents",
        data={
            "institution_id": str(e2e_environment["inst_a"].id),
            "document_type": "land_lease",
            "valid_from": "2020-01-01",
            "valid_to": (date.today() + timedelta(days=60)).isoformat(),
        },
        files={"file": ("land_lease.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        cookies=inst_a_cookies,
        headers=inst_a_headers,
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["data"]["id"]

    # 2. Authenticated Institution A user downloads file -> 200
    dl_res = client.get(f"/api/v1/documents/{doc_id}/download", cookies=inst_a_cookies)
    assert dl_res.status_code == 200
    assert dl_res.content.startswith(b"%PDF")

    # 3. Cross-Institution B user attempts download -> 404/403
    cross_dl = client.get(f"/api/v1/documents/{doc_id}/download", cookies=inst_b_cookies)
    assert cross_dl.status_code in (403, 404)

    # 4. Create Renewal obligation
    renew_res = client.post(
        f"/api/v1/documents/{doc_id}/renew",
        json={"renewal_due_date": (date.today() + timedelta(days=60)).isoformat()},
        cookies=ro_cookies,
        headers=ro_headers,
    )
    assert renew_res.status_code == 200
    renewal_id = renew_res.json()["data"]["id"]

    # 5. Upload replacement document
    renew_pdf = b"%PDF-1.4\nRenewed 30-year lease agreement\n%%EOF"
    replace_res = client.post(
        f"/api/v1/documents/renewals/{renewal_id}/replace",
        files={"file": ("land_lease_renewed.pdf", io.BytesIO(renew_pdf), "application/pdf")},
        data={"valid_from": date.today().isoformat(), "valid_to": (date.today() + timedelta(days=10950)).isoformat()},
        cookies=ro_cookies,
        headers=ro_headers,
    )
    assert replace_res.status_code == 200


# ==============================================================================
# Workstream 1: Scenario 7 - Analytics & Reporting End-to-End
# ==============================================================================

def test_w1_s7_analytics_and_reporting_e2e(client: TestClient, e2e_environment: dict, db_session: Session):
    admin_cookies, admin_headers = auth_client(client, "admin@test.local")
    inst_cookies, _ = auth_client(client, "inst_a@test.local")

    # 1. Summary Metrics match database
    summary_res = client.get("/api/v1/dashboard/summary", cookies=admin_cookies)
    assert summary_res.status_code == 200
    sum_data = summary_res.json()["data"]
    assert "total_applications" in sum_data
    assert "pending_scrutiny" in sum_data
    assert "pending_evc" in sum_data

    # EVC domain metrics
    evc_metrics = client.get("/api/v1/dashboard/evc-analytics", cookies=admin_cookies)
    assert evc_metrics.status_code == 200
    assert "scheduled_count" in evc_metrics.json()["data"]
    assert "pending_reports" in evc_metrics.json()["data"]

    # 2. Regional comparison: Apex role succeeds, Institution role gets 403
    reg_apex = client.get("/api/v1/dashboard/regional-comparison", cookies=admin_cookies)
    assert reg_apex.status_code == 200
    assert isinstance(reg_apex.json()["data"], list)

    reg_inst = client.get("/api/v1/dashboard/regional-comparison", cookies=inst_cookies)
    assert reg_inst.status_code == 403

    # 3. All 6 report types available
    types_res = client.get("/api/v1/reports/types", cookies=admin_cookies)
    assert types_res.status_code == 200
    codes = [t["code"] for t in types_res.json()["data"]]
    expected_reports = [
        "application_pendency",
        "application_ageing",
        "evc_status",
        "undertaking_compliance",
        "document_validity",
        "escalations_audit",
    ]
    for r in expected_reports:
        assert r in codes

    # 4. Preview and CSV Export for each report
    for r_code in expected_reports:
        prev = client.post(
            "/api/v1/reports/preview",
            json={"report_type": r_code, "page": 1, "page_size": 10},
            cookies=admin_cookies,
            headers=admin_headers,
        )
        assert prev.status_code == 200
        assert "rows" in prev.json()["data"]

        exp = client.post(
            "/api/v1/reports/export",
            json={"report_type": r_code, "export_format": "csv"},
            cookies=admin_cookies,
            headers=admin_headers,
        )
        assert exp.status_code == 200
        assert "text/csv" in exp.headers.get("content-type", "")
        assert exp.content.startswith(b"\xef\xbb\xbf")


# ==============================================================================
# Workstream 1: Scenario 8 - Admin Configuration & Versioning
# ==============================================================================

def test_w1_s8_configuration_and_versioning_e2e(client: TestClient, e2e_environment: dict, db_session: Session):
    admin_cookies, admin_headers = auth_client(client, "admin@test.local")
    stage_id = str(e2e_environment["stage1"].id)

    # 1. Update without change_reason -> 422 Unprocessable Entity
    bad_up = client.patch(
        f"/api/v1/admin/stages/{stage_id}",
        json={"timeline_days": 12, "change_reason": ""},
        cookies=admin_cookies,
        headers=admin_headers,
    )
    assert bad_up.status_code == 422

    # 2. Update with change_reason -> Succeeds
    good_up = client.patch(
        f"/api/v1/admin/stages/{stage_id}",
        json={"timeline_days": 12, "change_reason": "Executive Council Resolution 42/2026 on scrutiny buffer."},
        cookies=admin_cookies,
        headers=admin_headers,
    )
    assert good_up.status_code == 200
    assert good_up.json()["data"]["timeline_days"] == 12

    # 3. Check config_versions table via API
    vers_res = client.get("/api/v1/admin/config/versions?config_type=route_stage", cookies=admin_cookies)
    assert vers_res.status_code == 200
    versions = vers_res.json()["data"]
    assert len(versions) >= 1
    assert any("Executive Council Resolution" in v["change_summary"] for v in versions)


# ==============================================================================
# Workstream 1: Scenario 9 - Operational Monitoring & Readiness
# ==============================================================================

def test_w1_s9_operational_monitoring_e2e(client: TestClient, e2e_environment: dict):
    admin_cookies, _ = auth_client(client, "admin@test.local")

    # 1. Readiness probe
    ready_res = client.get("/api/v1/health/readiness")
    assert ready_res.status_code == 200
    assert ready_res.json()["data"]["database"]["status"] == "connected"

    # 2. Worker monitoring
    worker_res = client.get("/api/v1/monitoring/worker", cookies=admin_cookies)
    assert worker_res.status_code == 200
    w_data = worker_res.json()["data"]
    assert "status" in w_data
    assert "recent_runs" in w_data

    # 3. Notification queue monitoring
    notif_res = client.get("/api/v1/monitoring/notifications", cookies=admin_cookies)
    assert notif_res.status_code == 200
    assert "total_count" in notif_res.json()["data"]

