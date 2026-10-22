from datetime import date, datetime, timedelta, timezone
import io
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
    Document,
    DocumentRenewal,
    EVC,
    EVCMember,
    EVCReport,
    FileRecord,
    Institution,
    Region,
    ReminderRule,
    RouteStage,
    RouteType,
    SchedulerRun,
    Undertaking,
    UndertakingSubmission,
    User,
)
from backend.app.permissions.roles import UserRole
from backend.app.services.document_service import DocumentService
from backend.app.services.evc_service import EVCService
from backend.app.services.file_service import FileStorageService
from backend.app.services.undertaking_service import UndertakingService
from backend.app.services.workflow_service import WorkflowService
from worker.deadline_scan import execute_deadline_scan


@pytest.fixture
def phase5_test_setup(db_session: Session) -> Dict:
    """
    Sets up isolated test data for Phase 5 tests:
    - 2 Regions (North, South)
    - 2 Institutions (Alpha in North, Beta in South)
    - Route & Application
    - Users for all roles
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
        name="Engineering Approval",
        code="ROUTE_ENG",
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
        stage_code="STG_SCRUTINY",
        stage_name="Scrutiny",
        sequence=1,
        required_role=UserRole.SCRUTINY_OFFICER.value,
        timeline_days=7,
        day_type="working",
        is_required=True,
    )
    db_session.add(stage1)
    db_session.flush()

    # Users
    admin = User(
        id=uuid.uuid4(),
        email="admin@test.local",
        full_name="Admin User",
        password_hash=pw,
        role=UserRole.SYSTEM_ADMIN.value,
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
    committee_user = User(
        id=uuid.uuid4(),
        email="expert1@test.local",
        full_name="Expert Member",
        password_hash=pw,
        role=UserRole.COMMITTEE_MEMBER.value,
        is_active=True,
    )
    unassigned_committee = User(
        id=uuid.uuid4(),
        email="unassigned@test.local",
        full_name="Unassigned Member",
        password_hash=pw,
        role=UserRole.COMMITTEE_MEMBER.value,
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

    db_session.add_all([
        admin,
        ro_north,
        ro_south,
        inst_user_a,
        inst_user_b,
        committee_user,
        unassigned_committee,
        scrutiny_user,
    ])
    db_session.commit()

    # Create application for Inst A
    app_a = WorkflowService.create_application(
        db=db_session,
        user=inst_user_a,
        route_type_id=route.id,
        institution_id=inst_a.id,
    )
    db_session.commit()

    return {
        "region_north": r_north,
        "region_south": r_south,
        "inst_a": inst_a,
        "inst_b": inst_b,
        "app_a": app_a,
        "admin": admin,
        "ro_north": ro_north,
        "ro_south": ro_south,
        "inst_user_a": inst_user_a,
        "inst_user_b": inst_user_b,
        "committee_user": committee_user,
        "unassigned_committee": unassigned_committee,
        "scrutiny_user": scrutiny_user,
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
# 1. Secure File Handling Tests
# ==============================================================================

def test_file_upload_valid_pdf_and_checksum(client: TestClient, phase5_test_setup: dict):
    cookies, headers = login_helper(client, "inst_a@test.local")
    # Valid PDF content starting with %PDF
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    files = {"file": ("document.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {
        "institution_id": str(phase5_test_setup["inst_a"].id),
        "document_type": "land_lease",
        "valid_from": "2026-01-01",
        "valid_to": "2046-01-01",
    }
    res = client.post("/api/v1/documents", data=data, files=files, cookies=cookies, headers=headers)
    assert res.status_code == 200
    doc_data = res.json()["data"]
    assert doc_data["document_type"] == "land_lease"
    assert doc_data["checksum"] is not None
    assert doc_data["verification_status"] == "pending"


def test_file_upload_invalid_signature_rejected(client: TestClient, phase5_test_setup: dict):
    cookies, headers = login_helper(client, "inst_a@test.local")
    # File named document.pdf but containing plain text instead of %PDF magic bytes
    fake_pdf = b"This is not a real PDF file."
    files = {"file": ("document.pdf", io.BytesIO(fake_pdf), "application/pdf")}
    data = {
        "institution_id": str(phase5_test_setup["inst_a"].id),
        "document_type": "land_lease",
    }
    res = client.post("/api/v1/documents", data=data, files=files, cookies=cookies, headers=headers)
    assert res.status_code == 400
    assert "signature" in res.text.lower() or "not permitted" in res.text.lower()


def test_file_upload_disallowed_extension_rejected(client: TestClient, phase5_test_setup: dict):
    cookies, headers = login_helper(client, "inst_a@test.local")
    files = {"file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")}
    data = {
        "institution_id": str(phase5_test_setup["inst_a"].id),
        "document_type": "land_lease",
    }
    res = client.post("/api/v1/documents", data=data, files=files, cookies=cookies, headers=headers)
    assert res.status_code == 400
    assert "not permitted" in res.text.lower()


def test_file_upload_path_traversal_rejected(client: TestClient, phase5_test_setup: dict):
    cookies, headers = login_helper(client, "inst_a@test.local")
    files = {"file": ("../../etc/passwd.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")}
    data = {
        "institution_id": str(phase5_test_setup["inst_a"].id),
        "document_type": "land_lease",
    }
    res = client.post("/api/v1/documents", data=data, files=files, cookies=cookies, headers=headers)
    assert res.status_code == 400


# ==============================================================================
# 2. EVC Lifecycle & Scoping Tests
# ==============================================================================

def test_evc_creation_and_authorization(client: TestClient, phase5_test_setup: dict):
    # 1. Institution user cannot create EVC (Forbidden)
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    res_inst = client.post(
        "/api/v1/evc",
        json={"application_id": str(phase5_test_setup["app_a"].id)},
        cookies=cookies_inst,
        headers=headers_inst,
    )
    assert res_inst.status_code == 403

    # 2. Regional officer from south region cannot create EVC for north institution (Forbidden)
    cookies_ro_s, headers_ro_s = login_helper(client, "ro_south@test.local")
    res_ro_s = client.post(
        "/api/v1/evc",
        json={"application_id": str(phase5_test_setup["app_a"].id)},
        cookies=cookies_ro_s,
        headers=headers_ro_s,
    )
    assert res_ro_s.status_code == 403

    # 3. Regional officer for north region successfully queues EVC
    cookies_ro_n, headers_ro_n = login_helper(client, "ro_north@test.local")
    res_ro_n = client.post(
        "/api/v1/evc",
        json={"application_id": str(phase5_test_setup["app_a"].id), "notes": "EVC inspection required"},
        cookies=cookies_ro_n,
        headers=headers_ro_n,
    )
    assert res_ro_n.status_code == 200
    evc_data = res_ro_n.json()["data"]
    assert evc_data["status"] == "queued"


def test_evc_schedule_and_reschedule_with_mandatory_reason(client: TestClient, phase5_test_setup: dict, db_session: Session):
    evc = EVCService.create_evc(
        db=db_session,
        application_id=phase5_test_setup["app_a"].id,
        user=phase5_test_setup["ro_north"],
    )

    cookies_ro, headers_ro = login_helper(client, "ro_north@test.local")

    # 1. First scheduling: does not require reschedule reason
    first_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    res_sched = client.post(
        f"/api/v1/evc/{evc.id}/schedule",
        json={"scheduled_at": first_date, "notes": "Initial inspection schedule"},
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_sched.status_code == 200
    assert res_sched.json()["data"]["status"] == "scheduled"

    # 2. Rescheduling without reason must be rejected with 422
    second_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    res_no_reason = client.post(
        f"/api/v1/evc/{evc.id}/schedule",
        json={"scheduled_at": second_date, "notes": "Change date", "reason": "   "},
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_no_reason.status_code == 422

    # 3. Rescheduling with reason succeeds
    res_with_reason = client.post(
        f"/api/v1/evc/{evc.id}/schedule",
        json={
            "scheduled_at": second_date,
            "notes": "Postponed by 2 days",
            "reason": "Expert committee member emergency leave approved.",
        },
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_with_reason.status_code == 200
    assert res_with_reason.json()["data"]["scheduled_at"] is not None


def test_evc_committee_assignment_and_member_scoping(client: TestClient, phase5_test_setup: dict, db_session: Session):
    evc = EVCService.create_evc(
        db=db_session,
        application_id=phase5_test_setup["app_a"].id,
        user=phase5_test_setup["ro_north"],
    )
    cookies_ro, headers_ro = login_helper(client, "ro_north@test.local")

    # Assign committee member
    res_assign = client.post(
        f"/api/v1/evc/{evc.id}/members",
        json={
            "members": [
                {
                    "user_id": str(phase5_test_setup["committee_user"].id),
                    "member_name": "Dr. A. Sharma",
                    "member_role": "chairman",
                }
            ]
        },
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_assign.status_code == 200
    assert len(res_assign.json()["data"]["members"]) == 1

    # 1. Assigned committee member can view the EVC
    cookies_mem, _ = login_helper(client, "expert1@test.local")
    res_mem = client.get(f"/api/v1/evc/{evc.id}", cookies=cookies_mem)
    assert res_mem.status_code == 200

    # 2. Unassigned committee member CANNOT view the EVC (404 / inaccessible)
    cookies_unassigned, _ = login_helper(client, "unassigned@test.local")
    res_unassigned = client.get(f"/api/v1/evc/{evc.id}", cookies=cookies_unassigned)
    assert res_unassigned.status_code == 404


def test_evc_conduct_and_report_review(client: TestClient, phase5_test_setup: dict, db_session: Session):
    evc = EVCService.create_evc(
        db=db_session,
        application_id=phase5_test_setup["app_a"].id,
        user=phase5_test_setup["ro_north"],
    )
    EVCService.schedule_evc(
        db=db_session,
        evc_id=evc.id,
        user=phase5_test_setup["ro_north"],
        scheduled_at=datetime.now(timezone.utc),
    )
    EVCService.assign_members(
        db=db_session,
        evc_id=evc.id,
        user=phase5_test_setup["ro_north"],
        members_data=[{
            "user_id": phase5_test_setup["committee_user"].id,
            "member_name": "Dr. A. Sharma",
            "member_role": "chairman",
        }],
    )

    cookies_mem, headers_mem = login_helper(client, "expert1@test.local")

    # 1. Record conduct
    res_conduct = client.post(
        f"/api/v1/evc/{evc.id}/conduct",
        json={"notes": "Inspection completed successfully."},
        cookies=cookies_mem,
        headers=headers_mem,
    )
    assert res_conduct.status_code == 200
    assert res_conduct.json()["data"]["status"] == "conducted"

    # 2. Upload report
    pdf_bytes = b"%PDF-1.4\nEVC inspection report details\n%%EOF"
    files = {"file": ("evc_report.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_rep = client.post(f"/api/v1/evc/{evc.id}/report", files=files, cookies=cookies_mem, headers=headers_mem)
    assert res_rep.status_code == 200
    report_id = res_rep.json()["data"]["id"]

    # 3. RO reviews report (returns for correction first)
    cookies_ro, headers_ro = login_helper(client, "ro_north@test.local")
    res_rev = client.post(
        f"/api/v1/evc/reports/{report_id}/review",
        json={"decision": "returned_for_correction", "review_comments": "Clarify laboratory equipment counts."},
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_rev.status_code == 200
    assert res_rev.json()["data"]["review_status"] == "returned_for_correction"

    # 4. RO reviews revised report (accepts)
    res_accept = client.post(
        f"/api/v1/evc/reports/{report_id}/review",
        json={"decision": "accepted", "review_comments": "Laboratory discrepancy resolved; report complete."},
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_accept.status_code == 200
    assert res_accept.json()["data"]["review_status"] == "accepted"


# ==============================================================================
# 3. Undertaking Compliance & Dual-Control Verification Tests
# ==============================================================================

def test_undertaking_create_and_scoping(client: TestClient, phase5_test_setup: dict):
    # 1. Institution user cannot create undertaking
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    res_inst = client.post(
        "/api/v1/undertakings",
        json={
            "application_id": str(phase5_test_setup["app_a"].id),
            "title": "Faculty Cadre Rectification",
            "description": "Recruit 2 Associate Professors within 90 days",
            "due_date": (date.today() + timedelta(days=90)).isoformat(),
        },
        cookies=cookies_inst,
        headers=headers_inst,
    )
    assert res_inst.status_code == 403

    # 2. Regional officer creates undertaking
    cookies_ro, headers_ro = login_helper(client, "ro_north@test.local")
    res_ro = client.post(
        "/api/v1/undertakings",
        json={
            "application_id": str(phase5_test_setup["app_a"].id),
            "title": "Faculty Cadre Rectification",
            "description": "Recruit 2 Associate Professors within 90 days",
            "due_date": (date.today() + timedelta(days=90)).isoformat(),
        },
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_ro.status_code == 200
    assert res_ro.json()["data"]["status"] == "pending"


def test_undertaking_evidence_submission_and_dual_control_verification(
    client: TestClient, phase5_test_setup: dict, db_session: Session
):
    undertaking = UndertakingService.create_undertaking(
        db=db_session,
        application_id=phase5_test_setup["app_a"].id,
        title="Fire Safety NOC",
        description="Submit certified Fire Safety NOC",
        due_date=date.today() + timedelta(days=30),
        user=phase5_test_setup["ro_north"],
    )

    # 1. Institution Beta CANNOT submit evidence for Institution Alpha's undertaking
    cookies_b, headers_b = login_helper(client, "inst_b@test.local")
    pdf_bytes = b"%PDF-1.4\nNOC certificate\n%%EOF"
    files = {"file": ("fire_noc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_b = client.post(
        f"/api/v1/undertakings/{undertaking.id}/submit",
        files=files,
        data={"comments": "Beta trying to submit for Alpha"},
        cookies=cookies_b,
        headers=headers_b,
    )
    assert res_b.status_code in (403, 404)

    # 2. Institution Alpha submits evidence successfully
    cookies_a, headers_a = login_helper(client, "inst_a@test.local")
    files_a = {"file": ("fire_noc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_a = client.post(
        f"/api/v1/undertakings/{undertaking.id}/submit",
        files=files_a,
        data={"comments": "Certified NOC enclosed"},
        cookies=cookies_a,
        headers=headers_a,
    )
    assert res_a.status_code == 200
    sub_id = res_a.json()["data"]["id"]

    # 3. DUAL-CONTROL: Institution Alpha CANNOT verify its own submission!
    res_self_verify = client.post(
        f"/api/v1/undertakings/submissions/{sub_id}/review",
        json={"decision": "accepted", "review_comments": "Approving my own submission"},
        cookies=cookies_a,
        headers=headers_a,
    )
    assert res_self_verify.status_code == 403

    # 4. Regional officer verifies and accepts submission
    cookies_ro, headers_ro = login_helper(client, "ro_north@test.local")
    res_verify = client.post(
        f"/api/v1/undertakings/submissions/{sub_id}/review",
        json={"decision": "accepted", "review_comments": "NOC validity verified with state authority."},
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_verify.status_code == 200
    assert res_verify.json()["data"]["review_status"] == "accepted"


# ==============================================================================
# 4. Document Validity, Expiry Detection & Renewal Workflow Tests
# ==============================================================================

def test_document_validity_dates_and_expiry_detection(client: TestClient, phase5_test_setup: dict):
    cookies, headers = login_helper(client, "inst_a@test.local")

    # 1. Invalid date range (valid_from > valid_to) is rejected
    pdf_bytes = b"%PDF-1.4\nLand Lease\n%%EOF"
    files = {"file": ("lease.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data_invalid = {
        "institution_id": str(phase5_test_setup["inst_a"].id),
        "document_type": "land_lease",
        "valid_from": "2030-01-01",
        "valid_to": "2020-01-01",
    }
    res_inv = client.post("/api/v1/documents", data=data_invalid, files=files, cookies=cookies, headers=headers)
    assert res_inv.status_code == 400

    # 2. Upload document that is already expired
    files_exp = {"file": ("lease_expired.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data_exp = {
        "institution_id": str(phase5_test_setup["inst_a"].id),
        "document_type": "land_lease",
        "valid_from": "2000-01-01",
        "valid_to": "2020-01-01",  # in the past!
    }
    res_exp = client.post("/api/v1/documents", data=data_exp, files=files_exp, cookies=cookies, headers=headers)
    assert res_exp.status_code == 200
    assert res_exp.json()["data"]["is_expired"] is True


def test_document_renewal_preserves_version_history(client: TestClient, phase5_test_setup: dict, db_session: Session):
    cookies_inst, headers_inst = login_helper(client, "inst_a@test.local")
    pdf_v1 = b"%PDF-1.4\nLand lease version 1\n%%EOF"
    files_v1 = {"file": ("lease_v1.pdf", io.BytesIO(pdf_v1), "application/pdf")}
    data_v1 = {
        "institution_id": str(phase5_test_setup["inst_a"].id),
        "document_type": "land_lease",
        "valid_from": "2020-01-01",
        "valid_to": "2026-10-01",
    }
    res_v1 = client.post("/api/v1/documents", data=data_v1, files=files_v1, cookies=cookies_inst, headers=headers_inst)
    assert res_v1.status_code == 200
    doc_id = res_v1.json()["data"]["id"]

    # 1. Create renewal obligation
    cookies_ro, headers_ro = login_helper(client, "ro_north@test.local")
    res_renew = client.post(
        f"/api/v1/documents/{doc_id}/renew",
        json={"renewal_due_date": (date.today() + timedelta(days=60)).isoformat()},
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_renew.status_code == 200
    renewal_id = res_renew.json()["data"]["id"]

    # 2. Upload replacement document (version 2)
    pdf_v2 = b"%PDF-1.4\nLand lease version 2 renewed\n%%EOF"
    files_v2 = {"file": ("lease_v2_renewed.pdf", io.BytesIO(pdf_v2), "application/pdf")}
    data_v2 = {
        "valid_from": "2026-10-01",
        "valid_to": "2046-10-01",
    }
    res_replace = client.post(
        f"/api/v1/documents/renewals/{renewal_id}/replace",
        files=files_v2,
        data=data_v2,
        cookies=cookies_ro,
        headers=headers_ro,
    )
    assert res_replace.status_code == 200
    new_doc_id = res_replace.json()["data"]["id"]

    # 3. Verify history preservation: original document v1 still exists
    res_orig = client.get(f"/api/v1/documents/{doc_id}", cookies=cookies_ro)
    assert res_orig.status_code == 200
    assert len(res_orig.json()["data"]["renewals"]) == 1
    assert res_orig.json()["data"]["renewals"][0]["status"] == "completed"
    assert res_orig.json()["data"]["renewals"][0]["replacement_document_id"] == new_doc_id


def test_file_download_authorization(client: TestClient, phase5_test_setup: dict, db_session: Session):
    cookies_inst_a, headers_inst_a = login_helper(client, "inst_a@test.local")
    pdf_bytes = b"%PDF-1.4\nConfidential Alpha Document\n%%EOF"
    files = {"file": ("alpha_confidential.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {
        "institution_id": str(phase5_test_setup["inst_a"].id),
        "document_type": "building_safety",
    }
    res_upload = client.post("/api/v1/documents", data=data, files=files, cookies=cookies_inst_a, headers=headers_inst_a)
    doc_id = res_upload.json()["data"]["id"]

    # 1. Institution A downloads its own file successfully
    res_dl_a = client.get(f"/api/v1/documents/{doc_id}/download", cookies=cookies_inst_a)
    assert res_dl_a.status_code == 200
    assert b"Confidential Alpha Document" in res_dl_a.content

    # 2. Institution B attempt to download Institution A's file is FORBIDDEN (403 or 404)
    cookies_inst_b, _ = login_helper(client, "inst_b@test.local")
    res_dl_b = client.get(f"/api/v1/documents/{doc_id}/download", cookies=cookies_inst_b)
    assert res_dl_b.status_code in (403, 404)


# ==============================================================================
# 5. Worker Scan & Compliance Idempotency Tests
# ==============================================================================

def test_worker_scan_marks_overdue_undertakings(db_session: Session, phase5_test_setup: dict):
    # Create past-due undertaking
    past_due_date = date.today() - timedelta(days=5)
    u = UndertakingService.create_undertaking(
        db=db_session,
        application_id=phase5_test_setup["app_a"].id,
        title="Overdue Audit Statement",
        description="Audit statement submission",
        due_date=past_due_date,
        user=phase5_test_setup["ro_north"],
    )
    assert u.status == "pending"

    # Run worker scan
    run_res = execute_deadline_scan(db_session)
    assert run_res["status"] == "success"

    db_session.refresh(u)
    assert u.status == "overdue"
