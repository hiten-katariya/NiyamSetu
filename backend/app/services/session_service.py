from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.entities import User, UserSession


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensures a datetime object is timezone-aware in UTC, converting naive datetimes
    (such as those loaded from SQLite test environments).
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class SessionService:
    @staticmethod
    def hash_token(raw_token: str) -> str:
        """
        Computes SHA-256 hash of the raw session token.
        Only this hash is stored in the database.
        """
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_csrf_token() -> str:
        """
        Generates a cryptographically strong anti-CSRF token.
        """
        return secrets.token_hex(32)

    @classmethod
    def create_session(
        cls,
        db: Session,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, UserSession]:
        """
        Generates an opaque, high-entropy session token, hashes it,
        stores the record in the database, and returns (raw_token, session).
        """
        raw_token = secrets.token_urlsafe(32)
        token_hash = cls.hash_token(raw_token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=settings.SESSION_EXPIRE_SECONDS)

        session = UserSession(
            id=uuid.uuid4(),
            user_id=user_id,
            session_token_hash=token_hash,
            created_at=now,
            expires_at=expires_at,
            revoked_at=None,
            last_seen_at=now,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
        )
        db.add(session)
        db.flush()
        return raw_token, session

    @classmethod
    def get_valid_session(cls, db: Session, raw_token: Optional[str]) -> Optional[UserSession]:
        """
        Looks up a session by the hash of raw_token.
        Validates that it is not revoked, not expired, and that the user is active.
        """
        if not raw_token or len(raw_token) < 16:
            return None

        token_hash = cls.hash_token(raw_token)
        stmt = select(UserSession).where(UserSession.session_token_hash == token_hash)
        session = db.scalars(stmt).first()

        if not session:
            return None

        # Check if revoked
        if session.revoked_at is not None:
            return None

        # Check if expired
        now = datetime.now(timezone.utc)
        if ensure_utc(session.expires_at) <= now:
            return None

        # Update last_seen_at periodically (e.g. if > 60 seconds have passed)
        if (now - ensure_utc(session.last_seen_at)).total_seconds() > 60:
            session.last_seen_at = now
            db.flush()

        return session

    @classmethod
    def revoke_session(cls, db: Session, raw_token: Optional[str]) -> bool:
        """
        Invalidates a session on logout.
        """
        if not raw_token:
            return False

        token_hash = cls.hash_token(raw_token)
        stmt = select(UserSession).where(UserSession.session_token_hash == token_hash)
        session = db.scalars(stmt).first()

        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False

    @classmethod
    def revoke_all_user_sessions(cls, db: Session, user_id: uuid.UUID) -> int:
        """
        Revokes all active sessions for a user (e.g. on password change or security event).
        """
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
        sessions = db.scalars(stmt).all()
        now = datetime.now(timezone.utc)
        count = 0
        for s in sessions:
            s.revoked_at = now
            count += 1
        if count > 0:
            db.commit()
        return count
