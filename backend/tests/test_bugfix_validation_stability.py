from datetime import date, timedelta
import uuid
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import get_password_hash
from backend.app.models.entities import (
    Application,
    Holiday,
    Institution,
    Region,
    RouteStage,
    RouteType,
    Undertaking,
    User,
)
from backend.app.permissions.roles import UserRole


@pytest.fixture
def bugfix_setup(db_session: Session):
    """
    Sets up isolated test data for bugfix and validation regression tests.
    """
    pw = get_password_hash("ValidPassword123!")

    region = Region(id=uuid.uuid4(), name="Validation Region", code="REG_VAL", is_active=True)
    db_session.add(region)
    db_session.flush()

    inst = Institution(
        id=uuid.uuid4(),
        name="Validation Institute",
        institution_code="INST-VAL",
        region_id=region.id,
        contact_email="inst_val@test.local",
        is_active=True,
    )
    db_session.add(inst)
    db_session.flush()

    route = RouteType(id=uuid.uuid4(), name="Validation Route", code="VAL_ROUTE", current_version=1, is_active=True)
    db_session.add(route)
    db_session.flush()

    stage = RouteStage(
        id=uuid.uuid4(),
        route_type_id=route.id,
        route_version=1,
        stage_code="VAL_SCRUTINY",
        stage_name="Scrutiny Stage",
        sequence=1,
        required_role="scrutiny_officer",
        timeline_days=10,
        day_type="working_days",
        is_required=True,
    )
    db_session.add(stage)
    db_session.flush()

    admin_user = User(
        id=uuid.uuid4(),
        email="admin_val@test.local",
        password_hash=pw,
        full_name="Admin Val",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    officer_user = User(
        id=uuid.uuid4(),
        email="officer_val@test.local",
        password_hash=pw,
        full_name="Officer Val",
        role=UserRole.SCRUTINY_OFFICER.value,
        region_id=region.id,
        is_active=True,
    )
    inst_user = User(
        id=uuid.uuid4(),
        email="inst_user_val@test.local",
        password_hash=pw,
        full_name="Inst User Val",
        role=UserRole.INSTITUTION_USER.value,
        institution_id=inst.id,
        is_active=True,
    )
    db_session.add_all([admin_user, officer_user, inst_user])
    db_session.flush()

    from backend.app.services.workflow_service import WorkflowService
    app = WorkflowService.create_application(
        db=db_session,
        user=inst_user,
        route_type_id=route.id,
        institution_id=inst.id,
    )
    db_session.commit()

    return {
        "region": region,
        "inst": inst,
        "route": route,
        "app": app,
        "admin": admin_user,
        "officer": officer_user,
        "inst_user": inst_user,
    }


def login_as(client: TestClient, email: str, password: str = "ValidPassword123!"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    csrf_token = res.json()["data"]["csrf_token"]
    cookies = {
        settings.SESSION_COOKIE_NAME: res.cookies.get(settings.SESSION_COOKIE_NAME),
        settings.CSRF_COOKIE_NAME: res.cookies.get(settings.CSRF_COOKIE_NAME),
    }
    headers = {"X-CSRF-Token": csrf_token}
    return cookies, headers


def test_calendar_holiday_validation_success_and_failures(client: TestClient, bugfix_setup: dict, db_session: Session):
    """
    Validates holiday registration with short names/reasons, whitespace validation, and authorization.
    """
    cookies_admin, headers_admin = login_as(client, "admin_val@test.local")

    # 1. Success with brief 2-char name and brief justification (reported user input "dd")
    h_date = (date.today() + timedelta(days=20)).isoformat()
    res_ok = client.post(
        "/api/v1/admin/holidays",
        json={
            "name": "dd",
            "holiday_date": h_date,
            "change_reason": "dd",
        },
        cookies=cookies_admin,
        headers=headers_admin,
    )
    assert res_ok.status_code == 200, f"Holiday creation failed: {res_ok.text}"
    data = res_ok.json()["data"]
    assert data["name"] == "dd"
    assert data["holiday_date"] == h_date

    # 2. Failure: name with whitespace-only -> 422
    res_bad_name = client.post(
        "/api/v1/admin/holidays",
        json={
            "name": "  ",
            "holiday_date": h_date,
            "change_reason": "Valid reason",
        },
        cookies=cookies_admin,
        headers=headers_admin,
    )
    assert res_bad_name.status_code == 422
    assert "error" in res_bad_name.json()
    err_details = res_bad_name.json()["error"]["details"]
    assert any("name" in d.get("field", "") for d in err_details)

    # 3. Failure: empty change reason -> 422
    res_bad_reason = client.post(
        "/api/v1/admin/holidays",
        json={
            "name": "Valid Holiday",
            "holiday_date": h_date,
            "change_reason": "   ",
        },
        cookies=cookies_admin,
        headers=headers_admin,
    )
    assert res_bad_reason.status_code == 422
    err_details = res_bad_reason.json()["error"]["details"]
    assert any("change_reason" in d.get("field", "") for d in err_details)

    # 4. Unauthorized user cannot create holiday
    cookies_inst, headers_inst = login_as(client, "inst_user_val@test.local")
    res_forbidden = client.post(
        "/api/v1/admin/holidays",
        json={
            "name": "Unauthorized Holiday",
            "holiday_date": h_date,
            "change_reason": "Testing auth",
        },
        cookies=cookies_inst,
        headers=headers_inst,
    )
    assert res_forbidden.status_code == 403


def test_undertaking_issuance_contract_reconciliation(client: TestClient, bugfix_setup: dict, db_session: Session):
    """
    Validates undertaking creation with:
    - Canonical fields (title, description, application_id)
    - Frontend aliases (condition_title, condition_description, application_id=None scoped fallback)
    - Rejection of invalid inputs and institution role restrictions
    """
    cookies_officer, headers_officer = login_as(client, "officer_val@test.local")
    due = (date.today() + timedelta(days=30)).isoformat()
    app = bugfix_setup["app"]

    # 1. Success with canonical fields
    res_canonical = client.post(
        "/api/v1/undertakings",
        json={
            "application_id": str(app.id),
            "title": "Fire NOC Compliance",
            "description": "Submit updated statutory fire department clearance",
            "due_date": due,
        },
        cookies=cookies_officer,
        headers=headers_officer,
    )
    assert res_canonical.status_code == 200, f"Canonical undertaking failed: {res_canonical.text}"
    data_c = res_canonical.json()["data"]
    assert data_c["title"] == "Fire NOC Compliance"
    assert data_c["status"] == "pending"

    # 2. Success with frontend aliases and application_id omitted (reported user scenario)
    res_alias = client.post(
        "/api/v1/undertakings",
        json={
            "condition_title": "hdr6u",
            "condition_description": "vrdrb",
            "due_date": due,
            "institution_id": str(bugfix_setup["inst"].id),
        },
        cookies=cookies_officer,
        headers=headers_officer,
    )
    assert res_alias.status_code == 200, f"Alias undertaking failed: {res_alias.text}"
    data_a = res_alias.json()["data"]
    assert data_a["title"] == "hdr6u"
    assert data_a["description"] == "vrdrb"
    assert data_a["application_id"] == str(app.id)

    # 3. Failure on empty condition title -> 422
    res_bad_title = client.post(
        "/api/v1/undertakings",
        json={
            "condition_title": "  ",
            "condition_description": "Valid description",
            "due_date": due,
            "application_id": str(app.id),
        },
        cookies=cookies_officer,
        headers=headers_officer,
    )
    assert res_bad_title.status_code == 422

    # 4. Institution user cannot create undertaking
    cookies_inst, headers_inst = login_as(client, "inst_user_val@test.local")
    res_inst = client.post(
        "/api/v1/undertakings",
        json={
            "title": "Unauthorized Undertaking",
            "description": "Institution trying to issue condition",
            "due_date": due,
            "application_id": str(app.id),
        },
        cookies=cookies_inst,
        headers=headers_inst,
    )
    assert res_inst.status_code == 403


def test_paginated_api_consistency(client: TestClient, bugfix_setup: dict):
    """
    Verifies that applications, notifications, and escalations return consistent
    envelopes containing 'data' (List) and 'meta' (PaginationMeta).
    """
    cookies_officer, _ = login_as(client, "officer_val@test.local")

    # 1. Applications pagination
    res_apps = client.get("/api/v1/applications", cookies=cookies_officer)
    assert res_apps.status_code == 200
    json_apps = res_apps.json()
    assert "data" in json_apps and isinstance(json_apps["data"], list)
    assert "meta" in json_apps
    assert json_apps["meta"]["page"] == 1
    assert "total" in json_apps["meta"]
    assert "total_pages" in json_apps["meta"]

    # 2. Notifications pagination
    res_notifs = client.get("/api/v1/notifications", cookies=cookies_officer)
    assert res_notifs.status_code == 200
    json_notifs = res_notifs.json()
    assert "data" in json_notifs and isinstance(json_notifs["data"], list)
    assert "meta" in json_notifs

    # 3. Escalations pagination
    res_esc = client.get("/api/v1/escalations", cookies=cookies_officer)
    assert res_esc.status_code == 200
    json_esc = res_esc.json()
    assert "data" in json_esc and isinstance(json_esc["data"], list)
    assert "meta" in json_esc
