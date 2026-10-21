from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.entities import AuditLog

GENESIS_HASH = "0" * 64


def normalize_timestamp(dt: datetime) -> str:
    """
    Normalizes a datetime to UTC ISO string with millisecond/microsecond precision,
    ensuring identical string representation whether naive (e.g. SQLite) or timezone-aware.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class AuditService:
    @staticmethod
    def calculate_entry_hash(
        previous_hash: Optional[str],
        actor_user_id: Optional[uuid.UUID],
        action: str,
        entity_type: str,
        entity_id: str,
        occurred_at: datetime,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Computes SHA-256 entry hash linking to previous_hash to form a tamper-evident audit chain.
        """
        prev = previous_hash if previous_hash else GENESIS_HASH
        meta_str = json.dumps(metadata or {}, sort_keys=True)
        iso_time = normalize_timestamp(occurred_at)
        actor_str = str(actor_user_id) if actor_user_id else "system"
        payload = f"{prev}|{actor_str}|{action}|{entity_type}|{entity_id}|{iso_time}|{meta_str}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def record_action(
        cls,
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Appends an immutable audit log record linked to the previous log entry's hash.
        """
        # Get the latest audit log entry to link hashes
        stmt = select(AuditLog).order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc()).limit(1)
        last_entry = db.scalars(stmt).first()
        prev_hash = last_entry.entry_hash if last_entry else GENESIS_HASH

        now = datetime.now(timezone.utc)
        entry_hash = cls.calculate_entry_hash(
            previous_hash=prev_hash,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            occurred_at=now,
            metadata=metadata,
        )

        entry = AuditLog(
            id=uuid.uuid4(),
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            occurred_at=now,
            ip_address=ip_address,
            metadata_=metadata,
            previous_hash=prev_hash,
            entry_hash=entry_hash,
        )
        db.add(entry)
        db.flush()
        return entry

    @classmethod
    def verify_chain(cls, db: Session) -> Tuple[bool, Optional[str], int]:
        """
        Verifies the tamper-evident integrity of the audit log hash chain.
        Returns (is_valid, error_message, verified_count).
        """
        stmt = select(AuditLog).order_by(AuditLog.occurred_at.asc(), AuditLog.id.asc())
        entries = db.scalars(stmt).all()

        if not entries:
            return True, None, 0

        expected_prev = GENESIS_HASH
        for idx, entry in enumerate(entries):
            # Check link to previous hash
            if entry.previous_hash != expected_prev:
                return (
                    False,
                    f"Hash broken at entry index {idx} (ID {entry.id}): expected previous {expected_prev}, found {entry.previous_hash}",
                    idx,
                )

            # Re-calculate hash to ensure contents were not tampered with
            calculated = cls.calculate_entry_hash(
                previous_hash=entry.previous_hash,
                actor_user_id=entry.actor_user_id,
                action=entry.action,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                occurred_at=entry.occurred_at,
                metadata=entry.metadata_,
            )
            if calculated != entry.entry_hash:
                return (
                    False,
                    f"Tamper detected at entry index {idx} (ID {entry.id}): entry_hash does not match recomputed hash",
                    idx,
                )

            expected_prev = entry.entry_hash

        return True, None, len(entries)
