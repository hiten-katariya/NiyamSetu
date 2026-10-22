from datetime import datetime, timezone
from typing import Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import AppException, ForbiddenError, NotFoundError, UnauthorizedError
from backend.app.core.security import verify_password
from backend.app.models.entities import User, UserSession
from backend.app.permissions.rbac import validate_user_scope
from backend.app.permissions.roles import Permission, ROLE_PERMISSIONS, UserRole, normalize_role
from backend.app.schemas.auth import PermittedScope
from backend.app.services.audit_service import AuditService
from backend.app.services.rate_limiter import login_rate_limiter
from backend.app.services.session_service import SessionService


class AuthService:
    @staticmethod
    def authenticate_and_create_session(
        db: Session,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, str, UserSession]:
        """
        Authenticates user credentials, enforces rate limiting, updates last_login_at,
        creates a server-managed session with an opaque high-entropy token, and logs the outcome.
        Returns (user, raw_session_token, csrf_token, session).
        """
        normalized_email = email.lower().strip()
        rate_limit_key = f"{normalized_email}:{ip_address or 'local'}"

        # 1. Enforce login rate limiting
        if login_rate_limiter.is_rate_limited(rate_limit_key):
            raise AppException(
                message="Too many failed login attempts. Please try again in 5 minutes.",
                code="RATE_LIMITED",
                status_code=429,
            )

        # 2. Query user by normalized email
        stmt = select(User).where(User.email == normalized_email)
        user = db.scalars(stmt).first()

        # 3. Check account existence & credentials using generic failure response
        if not user:
            login_rate_limiter.record_failure(rate_limit_key)
            AuditService.record_action(
                db=db,
                action="LOGIN_FAILED",
                entity_type="user",
                entity_id=normalized_email,
                ip_address=ip_address,
                metadata={"reason": "invalid_credentials"},
            )
            db.commit()
            raise UnauthorizedError("Invalid email or password.")

        # 4. Check active account status
        if not user.is_active:
            login_rate_limiter.record_failure(rate_limit_key)
            AuditService.record_action(
                db=db,
                action="LOGIN_FAILED",
                entity_type="user",
                entity_id=str(user.id),
                actor_user_id=user.id,
                ip_address=ip_address,
                metadata={"reason": "account_inactive"},
            )
            db.commit()
            raise ForbiddenError("Account is inactive. Please contact the administrator.")

        # 5. Verify password hash
        if not verify_password(password, user.password_hash):
            login_rate_limiter.record_failure(rate_limit_key)
            AuditService.record_action(
                db=db,
                action="LOGIN_FAILED",
                entity_type="user",
                entity_id=str(user.id),
                actor_user_id=user.id,
                ip_address=ip_address,
                metadata={"reason": "invalid_credentials"},
            )
            db.commit()
            raise UnauthorizedError("Invalid email or password.")

        # Successful login: reset rate limiter failures
        login_rate_limiter.reset(rate_limit_key)

        # Update last login timestamp
        now = datetime.now(timezone.utc)
        user.last_login_at = now

        # Create server-managed session
        raw_token, session = SessionService.create_session(
            db=db,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        csrf_token = SessionService.generate_csrf_token()

        # Audit successful authentication (excluding passwords and token contents)
        AuditService.record_action(
            db=db,
            action="LOGIN_SUCCESS",
            entity_type="user",
            entity_id=str(user.id),
            actor_user_id=user.id,
            ip_address=ip_address,
            metadata={"session_id": str(session.id), "user_agent": user_agent[:100] if user_agent else None},
        )
        db.commit()

        return user, raw_token, csrf_token, session

    @staticmethod
    def terminate_session(
        db: Session,
        raw_token: Optional[str],
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Invalidates the session in the database and records audit trail.
        """
        if raw_token:
            SessionService.revoke_session(db, raw_token)
            if user:
                AuditService.record_action(
                    db=db,
                    action="LOGOUT",
                    entity_type="user",
                    entity_id=str(user.id),
                    actor_user_id=user.id,
                    ip_address=ip_address,
                    metadata={"reason": "user_initiated_logout"},
                )
                db.commit()

    @staticmethod
    def get_user_permitted_scope(user: User) -> PermittedScope:
        """
        Calculates and returns the user's authorized regional and institutional scope.
        """
        role_enum = normalize_role(user.role)

        if role_enum in (UserRole.ADMIN, UserRole.SYSTEM_ADMIN, UserRole.BUREAU_OFFICER, UserRole.SENIOR_AUTHORITY):
            return PermittedScope(
                is_global=True,
                region_id=user.region_id,
                institution_id=user.institution_id,
                scope_description="National / Bureau-wide administrative scope",
            )
        elif role_enum == UserRole.REGIONAL_OFFICER:
            return PermittedScope(
                is_global=False,
                region_id=user.region_id,
                institution_id=None,
                scope_description=f"Regional administrative scope (Region ID: {user.region_id})",
            )
        elif role_enum == UserRole.INSTITUTION_USER:
            return PermittedScope(
                is_global=False,
                region_id=user.region_id,
                institution_id=user.institution_id,
                scope_description=f"Institutional scope (Institution ID: {user.institution_id})",
            )
        elif role_enum == UserRole.COMMITTEE_MEMBER:
            return PermittedScope(
                is_global=False,
                region_id=user.region_id,
                institution_id=None,
                scope_description="Committee assignment scope (Assigned visits only)",
            )
        else:
            return PermittedScope(
                is_global=False,
                region_id=user.region_id,
                institution_id=user.institution_id,
                scope_description=f"Assigned scrutiny queue (Role: {user.role})",
            )

    @staticmethod
    def update_user_role(
        db: Session,
        target_user_id: uuid.UUID,
        new_role: str,
        actor_user: User,
        region_id: Optional[uuid.UUID] = None,
        institution_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
    ) -> User:
        """
        Privileged operation: changes a user's role and scopes, logging the change in audit trail.
        """
        target_user = db.get(User, target_user_id)
        if not target_user:
            raise NotFoundError("User not found.")

        role_enum = normalize_role(new_role)
        # Validate scope for the new role
        validate_user_scope(role_enum, region_id=region_id, institution_id=institution_id)

        old_role = target_user.role
        target_user.role = role_enum.value
        target_user.region_id = region_id
        target_user.institution_id = institution_id

        # Revoke existing sessions so permissions are refreshed on next login
        SessionService.revoke_all_user_sessions(db, target_user.id)

        AuditService.record_action(
            db=db,
            action="ROLE_CHANGE",
            entity_type="user",
            entity_id=str(target_user.id),
            actor_user_id=actor_user.id,
            ip_address=ip_address,
            metadata={"old_role": old_role, "new_role": role_enum.value},
        )
        db.commit()
        db.refresh(target_user)
        return target_user

    @staticmethod
    def update_account_status(
        db: Session,
        target_user_id: uuid.UUID,
        is_active: bool,
        actor_user: User,
        ip_address: Optional[str] = None,
    ) -> User:
        """
        Privileged operation: activates or deactivates a user account.
        Deactivating immediately terminates all active sessions for that user.
        """
        target_user = db.get(User, target_user_id)
        if not target_user:
            raise NotFoundError("User not found.")

        old_status = target_user.is_active
        target_user.is_active = is_active

        if not is_active:
            SessionService.revoke_all_user_sessions(db, target_user.id)

        AuditService.record_action(
            db=db,
            action="ACCOUNT_STATUS_CHANGE",
            entity_type="user",
            entity_id=str(target_user.id),
            actor_user_id=actor_user.id,
            ip_address=ip_address,
            metadata={"previous_status": old_status, "new_status": is_active},
        )
        db.commit()
        db.refresh(target_user)
        return target_user
