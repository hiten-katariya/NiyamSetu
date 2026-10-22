from datetime import datetime, timezone
import hashlib
import secrets
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
    EVC,
    EVCMember,
    Institution,
    Region,
    RouteStage,
    RouteType,
    StageHistory,
    User,
    UserSession,
)
from backend.app.permissions.roles import UserRole
from backend.app.services.workflow_service import WorkflowService


@pytest.fixture
def workflow_test_setup(db_session: Session) -> Dict:
    """
    Sets up isolated test data for Phase 3 workflow engine tests:
    - 2 Regions (North, South)
    - 2 Institutions (Inst A in North, Inst B in South)
    - 1 Active Route with 3 stages (Scrutiny -> Regional Review -> Final Decision Review)
    - 1 Inactive Route
    - Users for all test roles
    """
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

    # 3. Routes
    active_route = RouteType(
        id=uuid.uuid4(),
        name="Standard Review Route",
        code="ROUTE_STD",
        description="Standard 3-stage route",
        is_active=True,
        current_version=1,
    )
    inactive_route = RouteType(
        id=uuid.uuid4(),
        name="Deprecated Route",
        code="ROUTE_DEP",
        description="Inactive old route",
        is_active=False,
        current_version=1,
    )
    db_session.add_all([active_route, inactive_route])
    db_session.flush()

    # Stages for Active Route (v1)
    stage1 = RouteStage(
        id=uuid.uuid4(),
        route_type_id=active_route.id,
        route_version=1,
        stage_code="STG_SCRUTINY",
        stage_name="Document Scrutiny",
        sequence=1,
        required_role=UserRole.SCRUTINY_OFFICER.value,
        timeline_days=7,
        day_type="working",
        is_required=True,
    )
    stage2 = RouteStage(
        id=uuid.uuid4(),
        route_type_id=active_route.id,
        route_version=1,
        stage_code="STG_RO_REVIEW",
        stage_name="Regional Officer Review",
        sequence=2,
        required_role=UserRole.REGIONAL_OFFICER.value,
        timeline_days=5,
        day_type="working",
        is_required=True,
    )
    stage3 = RouteStage(
        id=uuid.uuid4(),
        route_type_id=active_route.id,
        route_version=1,
        stage_code="STG_FINAL",
        stage_name="Final Decision Review",
        sequence=3,
        required_role=UserRole.SENIOR_AUTHORITY.value,
        timeline_days=7,
        day_type="calendar",
        is_required=True,
    )
    db_session.add_all([stage1, stage2, stage3])
    db_session.flush()

    # 4. Users
    pw = get_password_hash("ValidPassword123!")

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
    committee_user = User(
        id=uuid.uuid4(),
        email="committee@test.local",
        full_name="Committee Member",
        password_hash=pw,
        role=UserRole.COMMITTEE_MEMBER.value,
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
        committee_user,
    ])
    db_session.commit()

    return {
        "region_north": r_north,
        "region_south": r_south,
        "inst_a": inst_a,
        "inst_b": inst_b,
        "active_route": active_route,
        "inactive_route": inactive_route,
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3,
        "admin": admin_user,
        "inst_user_a": inst_user_a,
        "inst_user_b": inst_user_b,
        "scrutiny_user": scrutiny_user,
        "ro_north": ro_north,
        "ro_south": ro_south,
        "senior_user": senior_user,
        "committee_user": committee_user,
    }


def login_helper(client: TestClient, email: str, password: str = "ValidPassword123!"):
    """Helper that logs in and returns session cookie dict and CSRF header dict."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    csrf_token = res.json()["data"]["csrf_token"]
    session_cookie = res.cookies.get(settings.SESSION_COOKIE_NAME)
    csrf_cookie = res.cookies.get(settings.CSRF_COOKIE_NAME)
    cookies = {settings.SESSION_COOKIE_NAME: session_cookie, settings.CSRF_COOKIE_NAME: csrf_cookie}
    headers = {"X-CSRF-Token": csrf_token}
    return cookies, headers


# ==============================================================================
# Phase 3 Workflow Engine Tests
# ==============================================================================

def test_workflow_routes_listing(client: TestClient, workflow_test_setup: dict):
    cookies, _ = login_helper(client, "admin@test.local")
    res = client.get("/api/v1/workflow/routes", cookies=cookies)
    assert res.status_code == 200
    data = res.json()["data"]
    codes = [r["code"] for r in data]
    assert "ROUTE_STD" in codes
    assert "ROUTE_DEP" not in codes  # Inactive route must not appear in active listings


def test_application_creation_active_route(client: TestClient, workflow_test_setup: dict, db_session: Session):
    cookies, headers = login_helper(client, "inst_a@test.local")
    route_id = str(workflow_test_setup["active_route"].id)

    res = client.post(
        "/api/v1/applications",
        json={"route_type_id": route_id},
        cookies=cookies,
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["reference_no"].startswith("NS-")
    assert data["status"] == "in_progress"
    assert data["route_version"] == 1
    assert data["current_stage_name"] == "Document Scrutiny"
    assert data["institution_name"] == "Institute Alpha"

    # Verify initial StageHistory entry
    app_id = uuid.UUID(data["id"])
    hist = db_session.query(StageHistory).filter_by(application_id=app_id).all()
    assert len(hist) == 1
    assert hist[0].action == "created"
    assert hist[0].from_stage_id is None
    assert hist[0].to_stage_id == workflow_test_setup["stage1"].id


def test_application_creation_inactive_route_rejected(client: TestClient, workflow_test_setup: dict):
    cookies, headers = login_helper(client, "inst_a@test.local")
    inactive_route_id = str(workflow_test_setup["inactive_route"].id)

    res = client.post(
        "/api/v1/applications",
        json={"route_type_id": inactive_route_id},
        cookies=cookies,
        headers=headers,
    )
    assert res.status_code == 400
    assert "inactive" in res.json()["error"]["message"].lower()


def test_institution_user_cannot_create_for_other_institution(client: TestClient, workflow_test_setup: dict):
    cookies, headers = login_helper(client, "inst_a@test.local")
    route_id = str(workflow_test_setup["active_route"].id)
    other_inst_id = str(workflow_test_setup["inst_b"].id)

    res = client.post(
        "/api/v1/applications",
        json={"route_type_id": route_id, "institution_id": other_inst_id},
        cookies=cookies,
        headers=headers,
    )
    assert res.status_code == 403


def test_valid_stage_advance(client: TestClient, workflow_test_setup: dict, db_session: Session):
    # 1. Create application by Inst A
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    # 2. Advance by Scrutiny Officer (authorized for stage 1)
    cookies_scrutiny, headers_scrutiny = login_helper(client, "scrutiny@test.local")
    adv_res = client.post(
        f"/api/v1/applications/{app_id}/advance",
        json={"comments": "All scrutiny documents verified"},
        cookies=cookies_scrutiny,
        headers=headers_scrutiny,
    )
    assert adv_res.status_code == 200
    adv_data = adv_res.json()["data"]
    assert adv_data["current_stage_code"] == "STG_RO_REVIEW"
    assert adv_data["current_stage_sequence"] == 2

    # Verify history
    hist = db_session.query(StageHistory).filter_by(application_id=uuid.UUID(app_id)).order_by(StageHistory.performed_at.asc()).all()
    assert len(hist) == 2
    assert hist[1].action == "advance"
    assert hist[1].from_stage_id == workflow_test_setup["stage1"].id
    assert hist[1].to_stage_id == workflow_test_setup["stage2"].id


def test_unauthorised_role_cannot_advance_stage(client: TestClient, workflow_test_setup: dict):
    # Create application at stage 1 (requires scrutiny_officer)
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    # Try advancing with RO North (not scrutiny officer)
    cookies_ro, headers_ro = login_helper(client, "ro_north@test.local")
    adv_res = client.post(
        f"/api/v1/applications/{app_id}/advance",
        json={"comments": "Premature attempt"},
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert adv_res.status_code == 403


def test_advance_from_final_stage_rejected(client: TestClient, workflow_test_setup: dict, db_session: Session):
    # Create application and manually move to stage 3 (final stage)
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    app = db_session.get(Application, uuid.UUID(app_id))
    app.current_stage_id = workflow_test_setup["stage3"].id
    db_session.commit()

    # Try advancing past stage 3 (final) with Senior Authority
    cookies_senior, headers_senior = login_helper(client, "senior@test.local")
    adv_res = client.post(
        f"/api/v1/applications/{app_id}/advance",
        json={"comments": "Advance beyond final"},
        cookies=cookies_senior,
        headers=headers_senior,
    )
    assert adv_res.status_code == 400
    assert "final stage" in adv_res.json()["error"]["message"].lower()


def test_return_requires_non_empty_reason(client: TestClient, workflow_test_setup: dict):
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    cookies_scrutiny, headers_scrutiny = login_helper(client, "scrutiny@test.local")
    # Empty reason
    ret_res = client.post(
        f"/api/v1/applications/{app_id}/return",
        json={"reason": "   "},
        cookies=cookies_scrutiny,
        headers=headers_scrutiny,
    )
    assert ret_res.status_code in (422, 400)


def test_return_with_authorised_reason_succeeds(client: TestClient, workflow_test_setup: dict, db_session: Session):
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    cookies_scrutiny, headers_scrutiny = login_helper(client, "scrutiny@test.local")
    ret_res = client.post(
        f"/api/v1/applications/{app_id}/return",
        json={"reason": "Land title deed document is missing required official seal."},
        cookies=cookies_scrutiny,
        headers=headers_scrutiny,
    )
    assert ret_res.status_code == 200
    assert ret_res.json()["data"]["status"] == "returned"

    # Verify history
    hist = db_session.query(StageHistory).filter_by(application_id=uuid.UUID(app_id)).order_by(StageHistory.performed_at.desc()).first()
    assert hist.action == "return"
    assert "seal" in hist.reason


def test_hold_requires_reason(client: TestClient, workflow_test_setup: dict):
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    cookies_scrutiny, headers_scrutiny = login_helper(client, "scrutiny@test.local")
    hold_res = client.post(
        f"/api/v1/applications/{app_id}/hold",
        json={"reason": "   "},
        cookies=cookies_scrutiny,
        headers=headers_scrutiny,
    )
    assert hold_res.status_code in (422, 400)


def test_hold_and_advance_prevention(client: TestClient, workflow_test_setup: dict):
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    cookies_scrutiny, headers_scrutiny = login_helper(client, "scrutiny@test.local")

    # 1. Place on hold
    hold_res = client.post(
        f"/api/v1/applications/{app_id}/hold",
        json={"reason": "Pending state government gazette notification clarification"},
        cookies=cookies_scrutiny,
        headers=headers_scrutiny,
    )
    assert hold_res.status_code == 200
    assert hold_res.json()["data"]["status"] == "on_hold"

    # 2. Advance while on hold must fail
    adv_res = client.post(
        f"/api/v1/applications/{app_id}/advance",
        json={"comments": "Try to advance while on hold"},
        cookies=cookies_scrutiny,
        headers=headers_scrutiny,
    )
    assert adv_res.status_code == 400
    assert "on hold" in adv_res.json()["error"]["message"].lower()


def test_resume_from_hold_succeeds(client: TestClient, workflow_test_setup: dict):
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    cookies_scrutiny, headers_scrutiny = login_helper(client, "scrutiny@test.local")
    client.post(
        f"/api/v1/applications/{app_id}/hold",
        json={"reason": "Temporary hold"},
        cookies=cookies_scrutiny,
        headers=headers_scrutiny,
    )

    # Resume
    resume_res = client.post(
        f"/api/v1/applications/{app_id}/resume",
        json={"comments": "Gazette notification verified, resuming scrutiny"},
        cookies=cookies_scrutiny,
        headers=headers_scrutiny,
    )
    assert resume_res.status_code == 200
    assert resume_res.json()["data"]["status"] == "in_progress"


def test_resume_when_not_on_hold_rejected(client: TestClient, workflow_test_setup: dict):
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    cookies_scrutiny, headers_scrutiny = login_helper(client, "scrutiny@test.local")
    res = client.post(
        f"/api/v1/applications/{app_id}/resume",
        json={"comments": "Invalid resume attempt"},
        cookies=cookies_scrutiny,
        headers=headers_scrutiny,
    )
    assert res.status_code == 400
    assert "not on hold" in res.json()["error"]["message"].lower()


def test_institution_user_cannot_return_hold_or_assign(client: TestClient, workflow_test_setup: dict):
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    # Return attempt by institution user -> 403
    ret_res = client.post(
        f"/api/v1/applications/{app_id}/return",
        json={"reason": "Self return"},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    assert ret_res.status_code == 403

    # Hold attempt by institution user -> 403
    hold_res = client.post(
        f"/api/v1/applications/{app_id}/hold",
        json={"reason": "Self hold"},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    assert hold_res.status_code == 403

    # Assign attempt by institution user -> 403
    assign_res = client.post(
        f"/api/v1/applications/{app_id}/assign",
        json={"target_user_id": str(workflow_test_setup["scrutiny_user"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    assert assign_res.status_code == 403


def test_institution_isolation_on_application_endpoints(client: TestClient, workflow_test_setup: dict):
    # Inst A creates an application
    cookies_a, headers_a = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_a,
        headers=headers_a,
    )
    app_a_id = create_res.json()["data"]["id"]

    # Inst B attempts to access Inst A's application -> 404 (does not disclose existence)
    cookies_b, _ = login_helper(client, "inst_b@test.local")
    get_res = client.get(f"/api/v1/applications/{app_a_id}", cookies=cookies_b)
    assert get_res.status_code == 404

    # Inst B list does not contain Inst A's application
    list_res = client.get("/api/v1/applications", cookies=cookies_b)
    assert list_res.status_code == 200
    ids = [item["id"] for item in list_res.json()["data"]]
    assert app_a_id not in ids


def test_regional_officer_scoping(client: TestClient, workflow_test_setup: dict):
    # Inst A is in North Region
    cookies_a, headers_a = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_a,
        headers=headers_a,
    )
    app_north_id = create_res.json()["data"]["id"]

    # RO North can access it
    cookies_ro_north, _ = login_helper(client, "ro_north@test.local")
    get_north = client.get(f"/api/v1/applications/{app_north_id}", cookies=cookies_ro_north)
    assert get_north.status_code == 200

    # RO South (different region) cannot access it -> 404
    cookies_ro_south, _ = login_helper(client, "ro_south@test.local")
    get_south = client.get(f"/api/v1/applications/{app_north_id}", cookies=cookies_ro_south)
    assert get_south.status_code == 404


def test_assignment_validation(client: TestClient, workflow_test_setup: dict):
    cookies_admin, headers_admin = login_helper(client, "admin@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={
            "route_type_id": str(workflow_test_setup["active_route"].id),
            "institution_id": str(workflow_test_setup["inst_a"].id),
        },
        cookies=cookies_admin,
        headers=headers_admin,
    )
    app_id = create_res.json()["data"]["id"]

    # 1. Valid assignment to Scrutiny Officer
    assign_res = client.post(
        f"/api/v1/applications/{app_id}/assign",
        json={"target_user_id": str(workflow_test_setup["scrutiny_user"].id), "notes": "Assigned for primary desk scrutiny"},
        cookies=cookies_admin,
        headers=headers_admin,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["data"]["assigned_to_name"] == "Scrutiny Officer"

    # 2. Cannot assign to institutional user -> 400
    fail_inst = client.post(
        f"/api/v1/applications/{app_id}/assign",
        json={"target_user_id": str(workflow_test_setup["inst_user_a"].id)},
        cookies=cookies_admin,
        headers=headers_admin,
    )
    assert fail_inst.status_code == 400

    # 3. Regional mismatch: cannot assign North institution app to RO South -> 400
    fail_ro = client.post(
        f"/api/v1/applications/{app_id}/assign",
        json={"target_user_id": str(workflow_test_setup["ro_south"].id)},
        cookies=cookies_admin,
        headers=headers_admin,
    )
    assert fail_ro.status_code == 400
    assert "regional" in fail_ro.json()["error"]["message"].lower()


def test_route_version_remains_pinned(client: TestClient, workflow_test_setup: dict, db_session: Session):
    # 1. Create application when route is version 1
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    # 2. Admin upgrades route configuration to version 2
    route = workflow_test_setup["active_route"]
    route.current_version = 2
    db_session.commit()

    # 3. Application detail still reflects version 1 and version 1 stages
    cookies_admin, _ = login_helper(client, "admin@test.local")
    detail_res = client.get(f"/api/v1/applications/{app_id}", cookies=cookies_admin)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert detail_data["route_version"] == 1
    assert len(detail_data["stages"]) == 3


def test_audit_log_recorded_for_transitions(client: TestClient, workflow_test_setup: dict, db_session: Session):
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    create_res = client.post(
        "/api/v1/applications",
        json={"route_type_id": str(workflow_test_setup["active_route"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    app_id = create_res.json()["data"]["id"]

    cookies_scrutiny, headers_scrutiny = login_helper(client, "scrutiny@test.local")
    client.post(
        f"/api/v1/applications/{app_id}/advance",
        json={"comments": "Passed scrutiny"},
        cookies=cookies_scrutiny,
        headers=headers_scrutiny,
    )

    # Verify audit events exist for APPLICATION_CREATED and APPLICATION_STAGE_ADVANCED
    events = db_session.query(AuditLog).filter_by(entity_id=app_id).all()
    actions = [e.action for e in events]
    assert "APPLICATION_CREATED" in actions
    assert "APPLICATION_STAGE_ADVANCED" in actions
