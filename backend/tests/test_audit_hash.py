from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session

from backend.app.models.entities import AuditLog
from backend.app.services.audit_service import AuditService, GENESIS_HASH


def test_audit_hash_calculation():
    now = datetime.now(timezone.utc)
    actor_id = uuid.uuid4()
    h1 = AuditService.calculate_entry_hash(
        previous_hash=GENESIS_HASH,
        actor_user_id=actor_id,
        action="CREATE_APPLICATION",
        entity_type="application",
        entity_id="app_123",
        occurred_at=now,
        metadata={"ref": "NS-001"},
    )
    assert len(h1) == 64

    # Different metadata should produce different hash
    h2 = AuditService.calculate_entry_hash(
        previous_hash=GENESIS_HASH,
        actor_user_id=actor_id,
        action="CREATE_APPLICATION",
        entity_type="application",
        entity_id="app_123",
        occurred_at=now,
        metadata={"ref": "NS-002"},
    )
    assert h1 != h2


def test_audit_chain_verification_intact(db_session: Session):
    actor_id = uuid.uuid4()

    # Record 3 actions
    AuditService.record_action(
        db=db_session,
        action="LOGIN",
        entity_type="user",
        entity_id=str(actor_id),
        actor_user_id=actor_id,
    )
    AuditService.record_action(
        db=db_session,
        action="CREATE_APPLICATION",
        entity_type="application",
        entity_id="NS-2026-01",
        actor_user_id=actor_id,
    )
    AuditService.record_action(
        db=db_session,
        action="ADVANCE_STAGE",
        entity_type="application",
        entity_id="NS-2026-01",
        actor_user_id=actor_id,
    )
    db_session.commit()

    is_valid, error, count = AuditService.verify_chain(db_session)
    assert is_valid is True
    assert error is None
    assert count == 3


def test_audit_chain_tamper_detection(db_session: Session):
    actor_id = uuid.uuid4()

    # Record 2 actions
    AuditService.record_action(
        db=db_session,
        action="LOGIN",
        entity_type="user",
        entity_id=str(actor_id),
        actor_user_id=actor_id,
    )
    AuditService.record_action(
        db=db_session,
        action="UPDATE_ROUTE",
        entity_type="route",
        entity_id="route_1",
        actor_user_id=actor_id,
    )
    db_session.commit()

    # Tamper with the second record directly in database
    log_entry = db_session.query(AuditLog).filter_by(action="UPDATE_ROUTE").first()
    assert log_entry is not None
    log_entry.action = "TAMPERED_ACTION"
    db_session.commit()

    # Chain verification should catch the modification
    is_valid, error, count = AuditService.verify_chain(db_session)
    assert is_valid is False
    assert "Tamper detected" in error or "Hash broken" in error
