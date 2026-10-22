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
    Holiday,
    Institution,
    MessageTemplate,
    Notification,
    Region,
    ReminderRule,
    RouteStage,
    RouteType,
    SchedulerRun,
    Undertaking,
    User,
)
from backend.app.permissions.roles import UserRole
from backend.app.services.report_service import sanitize_formula_injection
from backend.app.services.workflow_service import WorkflowService


@pytest.fixture
def phase6_test_setup(db_session: Session) -> Dict:
    """
    Sets up isolated test data for Phase 6 tests:
    - 2 Regions (North, South)
    - 2 Institutions (Alpha in North, Beta in South)
    - Route Type & Stages
    - Applications for both institutions
    - Users for Admin, Regional Officer, Institution User
    - Initial Reminder & Escalation rules, holidays, templates
    """
    pw = get_password_hash("ValidPassword123!")

    r_north = Region(id=uuid.uuid4(), name="North Region", code="REG_N", is_active=True)
    r_south = Region(id=uuid.uuid4(), name="South Region", code="REG_S", is_active=True)
    db_session.add_all([r_north, r_south])
    db_session.flush()

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

    route = RouteType(
        id=uuid.uuid4(),
        name="Standard Approval Route",
        code="STD_APPR",
        description="Standard approval route",
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
        stage_name="Scrutiny",
        sequence=1,
        required_role=UserRole.SCRUTINY_OFFICER.value,
        timeline_days=10,
        day_type="working_days",
        is_required=True,
    )
    stage2 = RouteStage(
        id=uuid.uuid4(),
        route_type_id=route.id,
        route_version=1,
        stage_code="EVC",
        stage_name="EVC Inspection",
        sequence=2,
        required_role=UserRole.REGIONAL_OFFICER.value,
        timeline_days=15,
        day_type="calendar_days",
        is_required=True,
    )
    db_session.add_all([stage1, stage2])
    db_session.flush()

    admin = User(
        id=uuid.uuid4(),
        email="admin_p6@test.local",
        full_name="Admin P6",
        password_hash=pw,
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    ro_north = User(
        id=uuid.uuid4(),
        email="ro_p6_north@test.local",
        full_name="RO North P6",
        password_hash=pw,
        role=UserRole.REGIONAL_OFFICER.value,
        region_id=r_north.id,
        is_active=True,
    )
    inst_user_a = User(
        id=uuid.uuid4(),
        email="inst_user_a_p6@test.local",
        full_name="Inst User Alpha P6",
        password_hash=pw,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_a.id,
        region_id=r_north.id,
        is_active=True,
    )
    db_session.add_all([admin, ro_north, inst_user_a])
    db_session.commit()

    # Application for Inst A
    app_a = WorkflowService.create_application(
        db=db_session,
        user=inst_user_a,
        route_type_id=route.id,
        institution_id=inst_a.id,
    )
    app_a.status = "in_progress"

    # Application for Inst B
    admin_inst_b = User(
        id=uuid.uuid4(),
        email="inst_user_b_p6@test.local",
        full_name="Inst User Beta P6",
        password_hash=pw,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_b.id,
        region_id=r_south.id,
        is_active=True,
    )
    db_session.add(admin_inst_b)
    db_session.flush()

    app_b = WorkflowService.create_application(
        db=db_session,
        user=admin_inst_b,
        route_type_id=route.id,
        institution_id=inst_b.id,
    )
    app_b.status = "completed"
    app_b.closed_at = datetime.now(timezone.utc)

    # Add EVC for app_a
    evc_a = EVC(
        id=uuid.uuid4(),
        application_id=app_a.id,
        status="scheduled",
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=5),
        assigned_region_id=r_north.id,
    )
    db_session.add(evc_a)

    # Add Undertaking for inst_a
    und_a = Undertaking(
        id=uuid.uuid4(),
        application_id=app_a.id,
        assigned_institution_id=inst_a.id,
        title="Fire Safety Rectification",
        description="Statutory Fire Safety NOC and equipment compliance",
        due_date=date.today() + timedelta(days=7),
        status="pending",
    )
    db_session.add(und_a)

    # Add Document for inst_a
    doc_a = Document(
        id=uuid.uuid4(),
        institution_id=inst_a.id,
        application_id=app_a.id,
        document_type="land_lease",
        original_filename="land_deed.pdf",
        storage_key="test_storage_key_doc_a",
        mime_type="application/pdf",
        size_bytes=1024,
        checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        valid_from=date.today() - timedelta(days=100),
        valid_to=date.today() + timedelta(days=1000),
        verification_status="verified",
    )
    db_session.add(doc_a)

    # Add Reminder & Escalation Rules
    rem_rule = ReminderRule(
        id=uuid.uuid4(),
        name="Stage Due in 3 Days",
        target_type="application",
        days_before_due=3,
        recipient_roles=["scrutiny_officer"],
        is_active=True,
    )
    esc_rule = EscalationRule(
        id=uuid.uuid4(),
        name="Stage Overdue Level 1",
        target_type="application",
        level=1,
        days_after_due=2,
        recipient_roles=["regional_officer"],
        is_active=True,
    )
    tpl = MessageTemplate(
        id=uuid.uuid4(),
        code="REMINDER_STAGE_DUE",
        channel="in_app",
        subject_template="Reminder: Stage Due Soon",
        body_template="Application {{ref}} is due in {{days}} days.",
        is_active=True,
    )
    db_session.add_all([rem_rule, esc_rule, tpl])
    db_session.commit()

    return {
        "admin": admin,
        "ro_north": ro_north,
        "inst_user_a": inst_user_a,
        "inst_a": inst_a,
        "inst_b": inst_b,
        "r_north": r_north,
        "r_south": r_south,
        "route": route,
        "stage1": stage1,
        "stage2": stage2,
        "app_a": app_a,
        "app_b": app_b,
        "rem_rule": rem_rule,
        "esc_rule": esc_rule,
        "tpl": tpl,
    }


def login_helper(client: TestClient, email: str, password: str = "ValidPassword123!"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    csrf_token = res.json()["data"]["csrf_token"]
    session_cookie = res.cookies.get(settings.SESSION_COOKIE_NAME)
    csrf_cookie = res.cookies.get(settings.CSRF_COOKIE_NAME)
    cookies = {settings.SESSION_COOKIE_NAME: session_cookie, settings.CSRF_COOKIE_NAME: csrf_cookie}
    headers = {"X-CSRF-Token": csrf_token}
    return cookies, headers


# ==============================================================================
# 1. Analytics & Dashboards Tests
# ==============================================================================

def test_dashboard_summary_with_query_filters(client: TestClient, phase6_test_setup: dict):
    cookies, headers = login_helper(client, "admin_p6@test.local")

    # Unfiltered summary
    res = client.get("/api/v1/dashboard/summary", cookies=cookies)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_applications"] >= 2
    assert data["in_progress"] >= 1
    assert data["completed_this_cycle"] >= 1

    # Filtered by status
    res_filt = client.get("/api/v1/dashboard/summary?status=completed", cookies=cookies)
    assert res_filt.status_code == 200
    assert res_filt.json()["data"]["total_applications"] >= 1


def test_volume_trends_endpoint(client: TestClient, phase6_test_setup: dict):
    cookies, headers = login_helper(client, "admin_p6@test.local")
    res = client.get("/api/v1/dashboard/volume-trends?days=14", cookies=cookies)
    assert res.status_code == 200
    trends = res.json()["data"]
    assert len(trends) == 15  # 14 days + today
    assert any(pt["submitted"] > 0 or pt["completed"] > 0 for pt in trends)


def test_regional_comparison_scoping_rules(client: TestClient, phase6_test_setup: dict):
    # 1. Institution user should be rejected (403 Forbidden)
    inst_cookies, _ = login_helper(client, "inst_user_a_p6@test.local")
    res_inst = client.get("/api/v1/dashboard/regional-comparison", cookies=inst_cookies)
    assert res_inst.status_code == 403

    # 2. Regional officer sees only their region
    ro_cookies, _ = login_helper(client, "ro_p6_north@test.local")
    res_ro = client.get("/api/v1/dashboard/regional-comparison", cookies=ro_cookies)
    assert res_ro.status_code == 200
    ro_data = res_ro.json()["data"]
    assert len(ro_data) == 1
    assert ro_data[0]["region_name"] == "North Region"

    # 3. Admin sees all regions
    admin_cookies, _ = login_helper(client, "admin_p6@test.local")
    res_admin = client.get("/api/v1/dashboard/regional-comparison", cookies=admin_cookies)
    assert res_admin.status_code == 200
    admin_data = res_admin.json()["data"]
    assert len(admin_data) >= 2


def test_evc_undertaking_document_and_ops_analytics(client: TestClient, phase6_test_setup: dict):
    cookies, _ = login_helper(client, "admin_p6@test.local")

    # EVC Analytics
    res_evc = client.get("/api/v1/dashboard/evc-analytics", cookies=cookies)
    assert res_evc.status_code == 200
    assert res_evc.json()["data"]["scheduled_count"] >= 1

    # Undertaking Analytics
    res_und = client.get("/api/v1/dashboard/undertaking-analytics", cookies=cookies)
    assert res_und.status_code == 200
    assert res_und.json()["data"]["pending_evidence"] >= 1

    # Document Analytics
    res_doc = client.get("/api/v1/dashboard/document-analytics", cookies=cookies)
    assert res_doc.status_code == 200
    assert res_doc.json()["data"]["valid_count"] >= 1

    # Operational Summary
    res_ops = client.get("/api/v1/dashboard/operational-summary", cookies=cookies)
    assert res_ops.status_code == 200
    assert "worker_status" in res_ops.json()["data"]


# ==============================================================================
# 2. Reporting & Safe Exports Tests
# ==============================================================================

def test_report_types_listing(client: TestClient, phase6_test_setup: dict):
    cookies, _ = login_helper(client, "admin_p6@test.local")
    res = client.get("/api/v1/reports/types", cookies=cookies)
    assert res.status_code == 200
    types = res.json()["data"]
    codes = [t["code"] for t in types]
    assert "application_pendency" in codes
    assert "application_ageing" in codes
    assert "evc_status" in codes
    assert "undertaking_compliance" in codes
    assert "document_validity" in codes
    assert "escalations_audit" in codes


def test_report_preview_and_pagination(client: TestClient, phase6_test_setup: dict):
    cookies, headers = login_helper(client, "admin_p6@test.local")
    payload = {
        "report_type": "application_pendency",
        "page": 1,
        "page_size": 10,
    }
    res = client.post("/api/v1/reports/preview", json=payload, cookies=cookies, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data["columns"]) >= 5
    assert data["total_rows"] >= 1
    assert len(data["rows"]) >= 1


def test_report_csv_export_and_formula_injection_defense(client: TestClient, phase6_test_setup: dict, db_session: Session):
    cookies, headers = login_helper(client, "admin_p6@test.local")

    # Formula injection unit check
    assert sanitize_formula_injection("=1+2") == "'=1+2"
    assert sanitize_formula_injection("+SUM(A1:A10)") == "'+SUM(A1:A10)"
    assert sanitize_formula_injection("-5") == "'-5"
    assert sanitize_formula_injection("@calc") == "'@calc"
    assert sanitize_formula_injection("Normal Text") == "Normal Text"

    payload = {
        "report_type": "application_pendency",
        "export_format": "csv",
    }
    res = client.post("/api/v1/reports/export", json=payload, cookies=cookies, headers=headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment; filename=" in res.headers["content-disposition"]

    # Verify UTF-8 BOM
    content_bytes = res.content
    assert content_bytes.startswith(b"\xef\xbb\xbf")

    # Verify audit log recorded for export
    audit_entry = db_session.scalar(
        AuditLog.__table__.select().where(AuditLog.action == "report_exported")
    )
    assert audit_entry is not None


# ==============================================================================
# 3. Configurable Administration Tests
# ==============================================================================

def test_admin_stage_update_requires_reason_and_creates_version(
    client: TestClient, phase6_test_setup: dict, db_session: Session
):
    cookies, headers = login_helper(client, "admin_p6@test.local")
    stage1 = phase6_test_setup["stage1"]

    # 1. Reject without change_reason
    res_no_reason = client.patch(
        f"/api/v1/admin/stages/{stage1.id}",
        json={"timeline_days": 12},
        cookies=cookies,
        headers=headers,
    )
    assert res_no_reason.status_code == 422

    # 2. Reject negative or 0 timeline days
    res_neg = client.patch(
        f"/api/v1/admin/stages/{stage1.id}",
        json={"timeline_days": 0, "change_reason": "Testing invalid zero"},
        cookies=cookies,
        headers=headers,
    )
    assert res_neg.status_code in (400, 422)

    # 3. Valid update
    res_valid = client.patch(
        f"/api/v1/admin/stages/{stage1.id}",
        json={"timeline_days": 14, "change_reason": "Adjusted scrutiny window per regional board"},
        cookies=cookies,
        headers=headers,
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["data"]["timeline_days"] == 14

    # Verify ConfigVersion entry
    ver = db_session.scalars(
        select(ConfigVersion).where(ConfigVersion.config_type == "route_stage")
    ).first()
    assert ver is not None
    assert "route_stage" in ver.config_type


def test_admin_reminder_and_escalation_rules_crud(client: TestClient, phase6_test_setup: dict):
    cookies, headers = login_helper(client, "admin_p6@test.local")

    # Create reminder rule
    rem_payload = {
        "name": "Phase 6 Alert",
        "target_type": "undertaking",
        "days_before_due": 5,
        "recipient_roles": ["institution_user"],
        "is_active": True,
        "change_reason": "Add 5-day warning for undertakings",
    }
    res_create = client.post("/api/v1/admin/rules/reminders", json=rem_payload, cookies=cookies, headers=headers)
    assert res_create.status_code == 200
    rule_id = res_create.json()["data"]["id"]

    # Update reminder rule
    rem_payload["days_before_due"] = 4
    rem_payload["change_reason"] = "Adjust to 4-day threshold"
    res_upd = client.put(f"/api/v1/admin/rules/reminders/{rule_id}", json=rem_payload, cookies=cookies, headers=headers)
    assert res_upd.status_code == 200
    assert res_upd.json()["data"]["days_before_due"] == 4

    # Delete reminder rule
    res_del = client.delete(
        f"/api/v1/admin/rules/reminders/{rule_id}?change_reason=Deprecated+rule",
        cookies=cookies,
        headers=headers,
    )
    assert res_del.status_code == 200


def test_admin_holidays_and_templates(client: TestClient, phase6_test_setup: dict):
    cookies, headers = login_helper(client, "admin_p6@test.local")

    # Add Holiday
    hol_payload = {
        "name": "Constitution Day",
        "holiday_date": "2026-11-26",
        "change_reason": "Statutory national holiday",
    }
    res_hol = client.post("/api/v1/admin/holidays", json=hol_payload, cookies=cookies, headers=headers)
    assert res_hol.status_code == 200
    hol_id = res_hol.json()["data"]["id"]

    # Delete Holiday
    res_del_hol = client.delete(
        f"/api/v1/admin/holidays/{hol_id}?change_reason=Rescheduled",
        cookies=cookies,
        headers=headers,
    )
    assert res_del_hol.status_code == 200

    # Update Message Template
    tpl = phase6_test_setup["tpl"]
    tpl_payload = {
        "subject_template": "Updated Reminder Subject",
        "body_template": "Updated message body template with {{ref}}.",
        "is_active": True,
        "change_reason": "Tone adjustment in notices",
    }
    res_tpl = client.put(
        f"/api/v1/admin/message-templates/{tpl.id}",
        json=tpl_payload,
        cookies=cookies,
        headers=headers,
    )
    assert res_tpl.status_code == 200
    assert res_tpl.json()["data"]["subject_template"] == "Updated Reminder Subject"


def test_config_versions_history_endpoint(client: TestClient, phase6_test_setup: dict):
    cookies, _ = login_helper(client, "admin_p6@test.local")
    res = client.get("/api/v1/admin/config/versions", cookies=cookies)
    assert res.status_code == 200
    assert isinstance(res.json()["data"], list)


# ==============================================================================
# 4. Audit & Operational Monitoring Tests
# ==============================================================================

def test_audit_log_search_and_scoping(client: TestClient, phase6_test_setup: dict):
    # Admin gets full logs
    admin_cookies, _ = login_helper(client, "admin_p6@test.local")
    res_admin = client.get("/api/v1/audit/logs?page=1&page_size=20", cookies=admin_cookies)
    assert res_admin.status_code == 200
    assert "data" in res_admin.json()
    assert "meta" in res_admin.json()

    # Institution user only gets scoped actions
    inst_cookies, _ = login_helper(client, "inst_user_a_p6@test.local")
    res_inst = client.get("/api/v1/audit/logs", cookies=inst_cookies)
    assert res_inst.status_code == 200


def test_audit_integrity_verification_endpoint(client: TestClient, phase6_test_setup: dict):
    cookies, _ = login_helper(client, "admin_p6@test.local")
    res = client.get("/api/v1/audit/verify-integrity", cookies=cookies)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is True
    assert data["verified_count"] >= 0


def test_worker_and_notification_monitoring(client: TestClient, phase6_test_setup: dict, db_session: Session):
    cookies, _ = login_helper(client, "admin_p6@test.local")

    # Add a mock scheduler run to verify monitoring output
    run = SchedulerRun(
        id=uuid.uuid4(),
        job_name="deadline_scan",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        finished_at=datetime.now(timezone.utc) - timedelta(minutes=4),
        status="success",
        items_scanned=20,
        items_processed=3,
    )
    db_session.add(run)
    db_session.commit()

    res_worker = client.get("/api/v1/monitoring/worker", cookies=cookies)
    assert res_worker.status_code == 200
    w_data = res_worker.json()["data"]
    assert w_data["status"] == "operational"
    assert w_data["total_runs"] >= 1
    assert w_data["last_successful_run"] is not None

    res_notif = client.get("/api/v1/monitoring/notifications", cookies=cookies)
    assert res_notif.status_code == 200
    assert "unread_count" in res_notif.json()["data"]


def test_csrf_protection_on_admin_mutations(client: TestClient, phase6_test_setup: dict):
    # Obtain session cookies but DO NOT provide X-CSRF-Token header
    cookies, _ = login_helper(client, "admin_p6@test.local")
    res = client.post(
        "/api/v1/admin/rules/reminders",
        json={"name": "No CSRF", "days_before_due": 1, "change_reason": "testing"},
        cookies=cookies,
        # Omit headers (no CSRF token)
    )
    assert res.status_code == 403
