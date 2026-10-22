from datetime import date, datetime, timedelta, timezone
import hashlib
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
    Document,
    EVC,
    FileRecord,
    Institution,
    Region,
    RouteStage,
    RouteType,
    Undertaking,
    User,
)
from backend.app.permissions.roles import UserRole
from backend.app.services.audit_service import AuditService
from backend.app.services.file_service import FileStorageService
from backend.app.services.report_service import sanitize_formula_injection


@pytest.fixture
def security_test_setup(db_session: Session) -> Dict:
    pw = get_password_hash("ValidPassword123!")

    # Regions
    r_north = Region(id=uuid.uuid4(), name="North Region", code="REG_N", is_active=True)
    r_south = Region(id=uuid.uuid4(), name="South Region", code="REG_S", is_active=True)
    db_session.add_all([r_north, r_south])
    db_session.flush()

    # Institutions
    inst_a = Institution(id=uuid.uuid4(), name="Inst A", institution_code="INST-A", region_id=r_north.id, contact_email="inst_a@test.local", is_active=True)
    inst_b = Institution(id=uuid.uuid4(), name="Inst B", institution_code="INST-B", region_id=r_south.id, contact_email="inst_b@test.local", is_active=True)
    db_session.add_all([inst_a, inst_b])
    db_session.flush()

    # Users
    user_inst_a = User(
        id=uuid.uuid4(),
        email="user_a@test.local",
        full_name="User Inst A",
        password_hash=pw,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_a.id,
        region_id=r_north.id,
        is_active=True,
    )
    user_inst_b = User(
        id=uuid.uuid4(),
        email="user_b@test.local",
        full_name="User Inst B",
        password_hash=pw,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_b.id,
        region_id=r_south.id,
        is_active=True,
    )
    ro_north = User(
        id=uuid.uuid4(),
        email="ro_n@test.local",
        full_name="RO North",
        password_hash=pw,
        role=UserRole.REGIONAL_OFFICER.value,
        region_id=r_north.id,
        is_active=True,
    )
    admin = User(
        id=uuid.uuid4(),
        email="admin_sec@test.local",
        full_name="Admin Sec",
        password_hash=pw,
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add_all([user_inst_a, user_inst_b, ro_north, admin])
    db_session.flush()

    # Routes & Stages
    route = RouteType(id=uuid.uuid4(), name="Sec Route", code="SEC_R", is_active=True, current_version=1)
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
        timeline_days=7,
        is_required=True,
    )
    db_session.add(stage1)
    db_session.flush()

    # Applications
    app_a = Application(
        id=uuid.uuid4(),
        reference_no="NS-SEC-A-01",
        institution_id=inst_a.id,
        route_type_id=route.id,
        route_version=1,
        current_stage_id=stage1.id,
        status="in_progress",
    )
    app_b = Application(
        id=uuid.uuid4(),
        reference_no="NS-SEC-B-01",
        institution_id=inst_b.id,
        route_type_id=route.id,
        route_version=1,
        current_stage_id=stage1.id,
        status="in_progress",
    )
    db_session.add_all([app_a, app_b])
    db_session.flush()

    # EVC for Inst B
    evc_b = EVC(
        id=uuid.uuid4(),
        application_id=app_b.id,
        status="scheduled",
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=4),
        assigned_region_id=r_south.id,
    )
    # Undertaking for Inst B
    und_b = Undertaking(
        id=uuid.uuid4(),
        application_id=app_b.id,
        assigned_institution_id=inst_b.id,
        title="Inst B Compliance Undertaking",
        description="Compliance undertaking description for Inst B",
        status="pending",
        due_date=date.today() + timedelta(days=30),
    )
    db_session.add_all([evc_b, und_b])
    db_session.commit()

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "user_inst_a": user_inst_a,
        "user_inst_b": user_inst_b,
        "ro_north": ro_north,
        "admin": admin,
        "app_a": app_a,
        "app_b": app_b,
        "evc_b": evc_b,
        "und_b": und_b,
    }


def login_user(client: TestClient, email: str):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "ValidPassword123!"})
    assert res.status_code == 200
    data = res.json()["data"]
    csrf_token = data["csrf_token"]
    cookies = {
        settings.SESSION_COOKIE_NAME: res.cookies.get(settings.SESSION_COOKIE_NAME),
        settings.CSRF_COOKIE_NAME: res.cookies.get(settings.CSRF_COOKIE_NAME),
    }
    headers = {"X-CSRF-Token": csrf_token}
    return cookies, headers


# ==============================================================================
# Workstream 2: Authorization and Tenant Isolation
# ==============================================================================

def test_unauthenticated_requests_rejected(client: TestClient):
    endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/applications"),
        ("GET", "/api/v1/evc"),
        ("GET", "/api/v1/undertakings"),
        ("GET", "/api/v1/documents"),
        ("GET", "/api/v1/dashboard/summary"),
        ("GET", "/api/v1/reports/types"),
        ("GET", "/api/v1/admin/config/versions"),
        ("GET", "/api/v1/audit/logs"),
        ("GET", "/api/v1/monitoring/worker"),
    ]
    for method, path in endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={})
        assert res.status_code == 401, f"Expected 401 for unauthenticated {method} {path}, got {res.status_code}"


def test_cross_institution_isolation(client: TestClient, security_test_setup: dict):
    # Inst User A tries to view Inst B's application
    cookies_a, _ = login_user(client, "user_a@test.local")
    app_b_id = str(security_test_setup["app_b"].id)
    evc_b_id = str(security_test_setup["evc_b"].id)
    und_b_id = str(security_test_setup["und_b"].id)

    # 1. Cross-institution Application access -> 403 or 404
    res_app = client.get(f"/api/v1/applications/{app_b_id}", cookies=cookies_a)
    assert res_app.status_code in (403, 404)

    # 2. Cross-institution EVC access -> 403 or 404
    res_evc = client.get(f"/api/v1/evc/{evc_b_id}", cookies=cookies_a)
    assert res_evc.status_code in (403, 404)

    # 3. Cross-institution Undertaking access -> 403 or 404
    res_und = client.get(f"/api/v1/undertakings/{und_b_id}", cookies=cookies_a)
    assert res_und.status_code in (403, 404)


def test_privilege_escalation_denied(client: TestClient, security_test_setup: dict):
    cookies_a, headers_a = login_user(client, "user_a@test.local")

    # 1. Non-admin attempts to view admin config versions -> 403
    res_conf = client.get("/api/v1/admin/config/versions", cookies=cookies_a)
    assert res_conf.status_code == 403

    # 2. Non-admin attempts to view worker monitoring -> 403
    res_mon = client.get("/api/v1/monitoring/worker", cookies=cookies_a)
    assert res_mon.status_code == 403

    # 3. Non-admin attempts to view notification queue monitoring -> 403
    res_notif = client.get("/api/v1/monitoring/notifications", cookies=cookies_a)
    assert res_notif.status_code == 403

    # 4. Non-admin attempts to create a reminder rule -> 403
    res_rule = client.post(
        "/api/v1/admin/rules/reminders",
        json={"name": "Hack", "target_type": "application", "days_before_due": 3, "change_reason": "Hack"},
        cookies=cookies_a,
        headers=headers_a,
    )
    assert res_rule.status_code == 403


# ==============================================================================
# Workstream 3: Security Assurance - File Storage & Input Hardening
# ==============================================================================

def test_file_upload_path_traversal_rejection(client: TestClient, security_test_setup: dict):
    cookies_a, headers_a = login_user(client, "user_a@test.local")
    fake_pdf = b"%PDF-1.4\nSafe content\n%%EOF"

    # Attempt path traversal via filename
    traversal_names = [
        "../../etc/passwd.pdf",
        "..\\..\\boot.ini.pdf",
        "nested/../../secret.pdf",
    ]
    for bad_name in traversal_names:
        res = client.post(
            "/api/v1/documents",
            data={
                "institution_id": str(security_test_setup["inst_a"].id),
                "document_type": "land_lease",
                "valid_from": "2026-01-01",
                "valid_to": "2036-01-01",
            },
            files={"file": (bad_name, io.BytesIO(fake_pdf), "application/pdf")},
            cookies=cookies_a,
            headers=headers_a,
        )
        assert res.status_code == 400
        assert "MALICIOUS_FILENAME" in res.text or "traversal" in res.text.lower()


def test_file_upload_mime_spoofing_magic_bytes_rejection(client: TestClient, security_test_setup: dict):
    cookies_a, headers_a = login_user(client, "user_a@test.local")

    # Spoofed file: .pdf extension but binary content is plain text / executable
    fake_executable = b"MZ\x90\x00\x03\x00\x00\x00"  # Windows PE header
    res = client.post(
        "/api/v1/documents",
        data={
            "institution_id": str(security_test_setup["inst_a"].id),
            "document_type": "land_lease",
            "valid_from": "2026-01-01",
            "valid_to": "2036-01-01",
        },
        files={"file": ("malicious.pdf", io.BytesIO(fake_executable), "application/pdf")},
        cookies=cookies_a,
        headers=headers_a,
    )
    assert res.status_code == 400
    assert "INVALID_FILE_SIGNATURE" in res.text


def test_formula_injection_sanitization():
    # Test all spreadsheet execution trigger characters: =, +, -, @, \t, \r
    test_cases = [
        ("=1+1", "'=1+1"),
        ("+cmd|' /C calc'!A0", "'+cmd|' /C calc'!A0"),
        ("-2+3", "'-2+3"),
        ("@SUM(A1:A10)", "'@SUM(A1:A10)"),
        ("\t=cmd|' /C calc'!A0", "'\t=cmd|' /C calc'!A0"),
        ("\r=1+1", "'\r=1+1"),
        ("  =SUM(A1:A10)", "'  =SUM(A1:A10)"),
        ("Normal Safe Text", "Normal Safe Text"),
        ("12345", "12345"),
        ("", ""),
    ]
    for input_val, expected in test_cases:
        actual = sanitize_formula_injection(input_val)
        assert actual == expected, f"Failed for input '{input_val}': got '{actual}', expected '{expected}'"


# ==============================================================================
# Workstream 3: Security Assurance - Audit Chain Integrity & Tamper Detection
# ==============================================================================

def test_audit_chain_tamper_detection(db_session: Session):
    """
    Verifies that the SHA-256 cryptographic chain detects deliberate database tampering.
    Tested in an isolated transaction fixture.
    """
    user_id = uuid.uuid4()
    app_id = str(uuid.uuid4())

    # 1. Create a pristine 3-entry chain
    log1 = AuditService.record_action(
        db=db_session,
        action="APPLICATION_CREATED",
        entity_type="application",
        entity_id=app_id,
        actor_user_id=user_id,
        metadata={"ref": "NS-001"},
    )
    log2 = AuditService.record_action(
        db=db_session,
        action="APPLICATION_TRANSITION",
        entity_type="application",
        entity_id=app_id,
        actor_user_id=user_id,
        metadata={"from": "DRAFT", "to": "SCRUTINY"},
    )
    log3 = AuditService.record_action(
        db=db_session,
        action="REPORT_EXPORTED",
        entity_type="report",
        entity_id="application_pendency",
        actor_user_id=user_id,
        metadata={"report": "application_pendency"},
    )
    db_session.commit()

    # Verify pristine chain passes
    is_valid, err, count = AuditService.verify_chain(db_session)
    assert is_valid is True
    assert count >= 3

    # 2. Deliberately tamper with log2 payload directly in database
    log2.metadata_ = {"from": "DRAFT", "to": "APPROVED_TAMPERED"}
    db_session.commit()

    # Re-verify -> Must detect chain corruption at log2
    is_valid_t, err_t, count_t = AuditService.verify_chain(db_session)
    assert is_valid_t is False
    assert err_t is not None
    assert "Tamper detected" in err_t or "Hash broken" in err_t
