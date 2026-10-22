from datetime import datetime, timedelta, timezone
import hashlib
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import get_password_hash
from backend.app.models.entities import (
    Application,
    AuditLog,
    EVC,
    EVCMember,
    Institution,
    Region,
    RouteStage,
    RouteType,
    User,
    UserSession,
)
from backend.app.permissions.roles import UserRole
from backend.app.services.rate_limiter import login_rate_limiter
from backend.app.services.session_service import SessionService


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    login_rate_limiter.clear_all()
    yield
    login_rate_limiter.clear_all()


@pytest.fixture
def test_setup_data(db_session: Session):
    """
    Sets up isolated test regions, institutions, route, and test users.
    """
    # 1. Regions
    r1 = Region(id=uuid.uuid4(), name="North Region", code="R_NORTH", is_active=True)
    r2 = Region(id=uuid.uuid4(), name="South Region", code="R_SOUTH", is_active=True)
    db_session.add_all([r1, r2])
    db_session.flush()

    # 2. Institutions
    inst_a = Institution(
        id=uuid.uuid4(),
        name="Institution Alpha",
        institution_code="INST-A",
        region_id=r1.id,
        contact_email="inst_a@test.edu",
        is_active=True,
    )
    inst_b = Institution(
        id=uuid.uuid4(),
        name="Institution Beta",
        institution_code="INST-B",
        region_id=r2.id,
        contact_email="inst_b@test.edu",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    db_session.flush()

    # 3. Route & Stage
    route = RouteType(id=uuid.uuid4(), name="Test Route", code="RT_TEST", is_active=True, current_version=1)
    db_session.add(route)
    db_session.flush()
    stage = RouteStage(
        id=uuid.uuid4(),
        route_type_id=route.id,
        route_version=1,
        stage_code="STG_1",
        stage_name="Stage 1",
        sequence=1,
        required_role="scrutiny_officer",
        timeline_days=7,
        day_type="calendar",
        is_required=True,
    )
    db_session.add(stage)
    db_session.flush()

    # 4. Users
    pw_hash = get_password_hash("ValidPassword123!")

    admin_user = User(
        id=uuid.uuid4(),
        full_name="Admin Test",
        email="admin@test.local",
        password_hash=pw_hash,
        role=UserRole.SYSTEM_ADMIN.value,
        is_active=True,
    )
    inst_a_user = User(
        id=uuid.uuid4(),
        full_name="User Alpha",
        email="user_a@test.local",
        password_hash=pw_hash,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_a.id,
        region_id=r1.id,
        is_active=True,
    )
    inst_b_user = User(
        id=uuid.uuid4(),
        full_name="User Beta",
        email="user_b@test.local",
        password_hash=pw_hash,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_b.id,
        region_id=r2.id,
        is_active=True,
    )
    ro_user_north = User(
        id=uuid.uuid4(),
        full_name="RO North",
        email="ro_north@test.local",
        password_hash=pw_hash,
        role=UserRole.REGIONAL_OFFICER.value,
        region_id=r1.id,
        is_active=True,
    )
    committee_user = User(
        id=uuid.uuid4(),
        full_name="Committee Member",
        email="comm@test.local",
        password_hash=pw_hash,
        role=UserRole.COMMITTEE_MEMBER.value,
        is_active=True,
    )
    inactive_user = User(
        id=uuid.uuid4(),
        full_name="Inactive User",
        email="inactive@test.local",
        password_hash=pw_hash,
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst_a.id,
        is_active=False,
    )

    db_session.add_all([admin_user, inst_a_user, inst_b_user, ro_user_north, committee_user, inactive_user])
    db_session.flush()

    # 5. Applications for Inst A and Inst B
    app_a = Application(
        id=uuid.uuid4(),
        reference_no="NS-TEST-A",
        institution_id=inst_a.id,
        route_type_id=route.id,
        route_version=1,
        current_stage_id=stage.id,
        status="in_progress",
    )
    app_b = Application(
        id=uuid.uuid4(),
        reference_no="NS-TEST-B",
        institution_id=inst_b.id,
        route_type_id=route.id,
        route_version=1,
        current_stage_id=stage.id,
        status="in_progress",
    )
    db_session.add_all([app_a, app_b])
    db_session.commit()

    return {
        "admin": admin_user,
        "inst_a_user": inst_a_user,
        "inst_b_user": inst_b_user,
        "ro_north": ro_user_north,
        "committee": committee_user,
        "inactive": inactive_user,
        "app_a": app_a,
        "app_b": app_b,
        "inst_a": inst_a,
        "inst_b": inst_b,
    }


# ==============================================================================
# 1. Authentication & Session Security Tests
# ==============================================================================

def test_valid_login_and_cookies(client: TestClient, test_setup_data: dict, db_session: Session):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "ValidPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["message"] == "Authentication successful"
    assert "csrf_token" in data
    assert data["user"]["email"] == "admin@test.local"
    assert "password_hash" not in data["user"]

    # Verify HttpOnly session cookie and accessible CSRF cookie
    session_cookie = response.cookies.get(settings.SESSION_COOKIE_NAME)
    csrf_cookie = response.cookies.get(settings.CSRF_COOKIE_NAME)
    assert session_cookie is not None
    assert csrf_cookie is not None

    # Verify session stored as hash in database (raw token not in db)
    token_hash = hashlib.sha256(session_cookie.encode("utf-8")).hexdigest()
    session_rec = db_session.query(UserSession).filter_by(session_token_hash=token_hash).first()
    assert session_rec is not None
    assert session_rec.user_id == test_setup_data["admin"].id
    assert session_rec.revoked_at is None
    expires_at = session_rec.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    assert expires_at > datetime.now(timezone.utc)


def test_invalid_password(client: TestClient, test_setup_data: dict):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    err = response.json()["error"]
    assert err["code"] == "UNAUTHORIZED"
    assert err["message"] == "Invalid email or password."


def test_unknown_account_generic_error(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.local", "password": "SomePassword123!"},
    )
    assert response.status_code == 401
    err = response.json()["error"]
    assert err["code"] == "UNAUTHORIZED"
    assert err["message"] == "Invalid email or password."


def test_inactive_account_rejection(client: TestClient, test_setup_data: dict):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@test.local", "password": "ValidPassword123!"},
    )
    assert response.status_code == 403
    err = response.json()["error"]
    assert "inactive" in err["message"].lower()


def test_logout_invalidates_session(client: TestClient, test_setup_data: dict, db_session: Session):
    # 1. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "ValidPassword123!"},
    )
    assert login_res.status_code == 200
    csrf_token = login_res.json()["data"]["csrf_token"]
    raw_session = login_res.cookies.get(settings.SESSION_COOKIE_NAME)

    # 2. Logout with CSRF header
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout_res.status_code == 200

    # 3. Verify session is revoked in database
    token_hash = hashlib.sha256(raw_session.encode("utf-8")).hexdigest()
    session_rec = db_session.query(UserSession).filter_by(session_token_hash=token_hash).first()
    assert session_rec is not None
    assert session_rec.revoked_at is not None

    # 4. Subsequent access with revoked session returns 401
    me_res = client.get("/api/v1/auth/me", cookies={settings.SESSION_COOKIE_NAME: raw_session})
    assert me_res.status_code == 401


def test_expired_session_rejection(client: TestClient, test_setup_data: dict, db_session: Session):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "ValidPassword123!"},
    )
    raw_session = login_res.cookies.get(settings.SESSION_COOKIE_NAME)

    # Manually expire session in DB
    token_hash = hashlib.sha256(raw_session.encode("utf-8")).hexdigest()
    session_rec = db_session.query(UserSession).filter_by(session_token_hash=token_hash).first()
    session_rec.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    # Access /auth/me with expired session -> 401
    me_res = client.get("/api/v1/auth/me", cookies={settings.SESSION_COOKIE_NAME: raw_session})
    assert me_res.status_code == 401
    assert "expired" in me_res.json()["error"]["message"].lower()


def test_unauthenticated_access_to_protected_endpoints(client: TestClient):
    endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/applications"),
        ("GET", "/api/v1/dashboard/summary"),
        ("GET", "/api/v1/admin/users"),
    ]
    for method, path in endpoints:
        res = client.request(method, path)
        assert res.status_code in (401, 403), f"Expected 401/403 on {method} {path}, got {res.status_code}"


def test_csrf_protection_on_state_changing_requests(client: TestClient, test_setup_data: dict):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "ValidPassword123!"},
    )
    session_cookie = login_res.cookies.get(settings.SESSION_COOKIE_NAME)
    csrf_cookie = login_res.cookies.get(settings.CSRF_COOKIE_NAME)

    # 1. State-changing request without X-CSRF-Token header -> 403 CSRF_VALIDATION_FAILED
    fail_res = client.post(
        "/api/v1/auth/logout",
        cookies={settings.SESSION_COOKIE_NAME: session_cookie, settings.CSRF_COOKIE_NAME: csrf_cookie},
    )
    assert fail_res.status_code == 403
    assert fail_res.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"

    # 2. State-changing request with mismatched X-CSRF-Token header -> 403
    mismatch_res = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": "invalid-token"},
        cookies={settings.SESSION_COOKIE_NAME: session_cookie, settings.CSRF_COOKIE_NAME: csrf_cookie},
    )
    assert mismatch_res.status_code == 403

    # 3. State-changing request with matching header and cookie -> 200 OK
    ok_res = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_cookie},
        cookies={settings.SESSION_COOKIE_NAME: session_cookie, settings.CSRF_COOKIE_NAME: csrf_cookie},
    )
    assert ok_res.status_code == 200


def test_login_rate_limiting(client: TestClient, test_setup_data: dict):
    # 5 failed attempts allowed, 6th should be rejected with 429
    for i in range(settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.local", "password": "BadPassword!"},
        )
        assert res.status_code == 401

    # 6th attempt should be rate limited
    limit_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "BadPassword!"},
    )
    assert limit_res.status_code == 429
    assert limit_res.json()["error"]["code"] == "RATE_LIMITED"


# ==============================================================================
# 2. Authorization & Scoping Tests
# ==============================================================================

def test_role_based_permission_enforcement(client: TestClient, test_setup_data: dict):
    # 1. Institution user accessing admin endpoint -> 403
    login_inst = client.post(
        "/api/v1/auth/login",
        json={"email": "user_a@test.local", "password": "ValidPassword123!"},
    )
    inst_cookie = login_inst.cookies.get(settings.SESSION_COOKIE_NAME)

    res_forbidden = client.get(
        "/api/v1/admin/users",
        cookies={settings.SESSION_COOKIE_NAME: inst_cookie},
    )
    assert res_forbidden.status_code == 403

    # 2. Admin user accessing admin endpoint -> 200
    login_admin = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "ValidPassword123!"},
    )
    admin_cookie = login_admin.cookies.get(settings.SESSION_COOKIE_NAME)

    res_allowed = client.get(
        "/api/v1/admin/users",
        cookies={settings.SESSION_COOKIE_NAME: admin_cookie},
    )
    assert res_allowed.status_code == 200
    assert len(res_allowed.json()["data"]) > 0


def test_institution_isolation(client: TestClient, test_setup_data: dict):
    """
    Institution A user must NOT be able to access Institution B's application.
    """
    # Login as User A
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "user_a@test.local", "password": "ValidPassword123!"},
    )
    cookie_a = login_res.cookies.get(settings.SESSION_COOKIE_NAME)

    # User A lists applications -> only sees App A
    list_res = client.get(
        "/api/v1/applications",
        cookies={settings.SESSION_COOKIE_NAME: cookie_a},
    )
    assert list_res.status_code == 200
    data = list_res.json()["data"]
    app_refs = [a["reference_no"] for a in data]
    assert "NS-TEST-A" in app_refs
    assert "NS-TEST-B" not in app_refs

    # User A directly requests App B by ID -> 404 (does not disclose existence)
    app_b_id = str(test_setup_data["app_b"].id)
    get_res = client.get(
        f"/api/v1/applications/{app_b_id}",
        cookies={settings.SESSION_COOKIE_NAME: cookie_a},
    )
    assert get_res.status_code == 404


def test_regional_user_scoping(client: TestClient, test_setup_data: dict):
    """
    Regional officer for North (Region 1) cannot access South (Region 2) application.
    """
    login_ro = client.post(
        "/api/v1/auth/login",
        json={"email": "ro_north@test.local", "password": "ValidPassword123!"},
    )
    cookie_ro = login_ro.cookies.get(settings.SESSION_COOKIE_NAME)

    # RO North lists applications -> sees App A (North), but not App B (South)
    list_res = client.get(
        "/api/v1/applications",
        cookies={settings.SESSION_COOKIE_NAME: cookie_ro},
    )
    assert list_res.status_code == 200
    refs = [a["reference_no"] for a in list_res.json()["data"]]
    assert "NS-TEST-A" in refs
    assert "NS-TEST-B" not in refs

    # Directly requesting App B returns 404
    app_b_id = str(test_setup_data["app_b"].id)
    get_res = client.get(
        f"/api/v1/applications/{app_b_id}",
        cookies={settings.SESSION_COOKIE_NAME: cookie_ro},
    )
    assert get_res.status_code == 404


def test_committee_member_unassigned_records(client: TestClient, test_setup_data: dict):
    """
    Committee member has access only to applications with assigned EVC inspections.
    """
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "comm@test.local", "password": "ValidPassword123!"},
    )
    cookie_comm = login_res.cookies.get(settings.SESSION_COOKIE_NAME)

    # When unassigned, lists zero applications
    list_res = client.get(
        "/api/v1/applications",
        cookies={settings.SESSION_COOKIE_NAME: cookie_comm},
    )
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 0


def test_unauthorized_role_changes_rejected(client: TestClient, test_setup_data: dict, db_session: Session):
    # 1. Non-admin trying to update role -> 403
    login_user = client.post(
        "/api/v1/auth/login",
        json={"email": "user_a@test.local", "password": "ValidPassword123!"},
    )
    cookie_user = login_user.cookies.get(settings.SESSION_COOKIE_NAME)
    csrf_user = login_user.json()["data"]["csrf_token"]

    target_id = str(test_setup_data["inst_b_user"].id)
    res_unauth = client.patch(
        f"/api/v1/admin/users/{target_id}/role",
        json={"role": "system_admin"},
        headers={"X-CSRF-Token": csrf_user},
        cookies={settings.SESSION_COOKIE_NAME: cookie_user, settings.CSRF_COOKIE_NAME: csrf_user},
    )
    assert res_unauth.status_code == 403

    # 2. Admin successfully updating role
    login_admin = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "ValidPassword123!"},
    )
    cookie_admin = login_admin.cookies.get(settings.SESSION_COOKIE_NAME)
    csrf_admin = login_admin.json()["data"]["csrf_token"]

    res_auth = client.patch(
        f"/api/v1/admin/users/{target_id}/role",
        json={"role": "scrutiny_officer"},
        headers={"X-CSRF-Token": csrf_admin},
        cookies={settings.SESSION_COOKIE_NAME: cookie_admin, settings.CSRF_COOKIE_NAME: csrf_admin},
    )
    assert res_auth.status_code == 200
    assert res_auth.json()["data"]["role"] == "scrutiny_officer"


# ==============================================================================
# 3. Audit Log Tests
# ==============================================================================

def test_audit_events_exclude_secrets(client: TestClient, test_setup_data: dict, db_session: Session):
    # Perform login
    client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "ValidPassword123!"},
    )
    # Perform failed login
    client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "SecretWrongPassword123!"},
    )

    # Check audit logs in database
    logs = db_session.query(AuditLog).all()
    assert len(logs) > 0

    for log in logs:
        log_str = str(log.metadata_) + str(log.action)
        # Verify passwords, hashes, and session cookies are never logged
        assert "ValidPassword123!" not in log_str
        assert "SecretWrongPassword123!" not in log_str
        assert "password_hash" not in log_str
        assert "niyamsetu_session" not in log_str
