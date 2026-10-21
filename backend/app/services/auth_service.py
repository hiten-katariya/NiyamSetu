from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, verify_password
from backend.app.models.entities import User
from backend.app.permissions.roles import ROLE_PERMISSIONS, UserRole


class AuthService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        user = db.scalars(stmt).first()
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        return user

    @staticmethod
    def create_user_token(user: User) -> dict:
        role_enum = UserRole(user.role) if user.role in UserRole.all_roles() else UserRole.INSTITUTION_USER
        perms = [p.value for p in ROLE_PERMISSIONS.get(role_enum, set())]

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "region_id": str(user.region_id) if user.region_id else None,
            "institution_id": str(user.institution_id) if user.institution_id else None,
        }
        token = create_access_token(token_data)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 3600,
            "permissions": perms,
        }
